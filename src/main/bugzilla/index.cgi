#!/usr/bin/perl -wT
# -*- Mode: perl; indent-tabs-mode: nil -*-
#
# The contents of this file are subject to the Mozilla Public
# License Version 1.1 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS
# IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
# implied. See the License for the specific language governing
# rights and limitations under the License.
#
# The Original Code is the Bugzilla Bug Tracking System.
#
# The Initial Developer of the Original Code is Netscape Communications
# Corporation. Portions created by Netscape are
# Copyright (C) 1998 Netscape Communications Corporation. All
# Rights Reserved.
#
# Contributor(s): Jacob Steenhagen <jake@bugzilla.org>
#                 Frédéric Buclin <LpSolit@gmail.com>

###############################################################################
# Script Initialization
###############################################################################

# Make it harder for us to do dangerous things in Perl.
use strict;

# Include the Bugzilla CGI and general utility library.
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;
use Bugzilla::Error;
use Bugzilla::Update;
use Bugzilla::Menu;

# Check whether or not the user is logged in
my $user = Bugzilla->login(LOGIN_REQUIRED);
my $cgi = Bugzilla->cgi;
my $template = Bugzilla->template;
my $vars = {};

# And log out the user if requested. We do this first so that nothing
# else accidentally relies on the current login.
if ($cgi->param('logout')) {
    Bugzilla->logout();
    $user = Bugzilla->user;
    $vars->{'message'} = "logged_out";
    # Make sure that templates or other code doesn't get confused about this.
    $cgi->delete('logout');
}

###############################################################################
# Main Body Execution
###############################################################################

# Force to use HTTPS unless Bugzilla->params->{'ssl'} equals 'never'.
# This is required because the user may want to log in from here.
if ($cgi->protocol ne 'https' && Bugzilla->params->{'sslbase'} ne ''
    && Bugzilla->params->{'ssl'} ne 'never')
{
    $cgi->require_https(Bugzilla->params->{'sslbase'});
}

my $vars = Bugzilla::Menu::PopulateClassificationAndProducts();

# Return the appropriate HTTP response headers.
print $cgi->header();

if ($user->in_group('admin')) {
    # If 'urlbase' is not set, display the Welcome page.
    unless (Bugzilla->params->{'urlbase'}) {
        $template->process('welcome-admin.html.tmpl')
          || ThrowTemplateError($template->error());
        exit;
    }
    # Inform the administrator about new releases, if any.
    $vars->{'release'} = Bugzilla::Update::get_notifications();
}

###############################################################################
# User Homepage
###############################################################################
my $dbh = Bugzilla->dbh;

if ($user->id) {
	
	my %homepage = ();
	my $user_homepage = $user->homepage;
	if ($user_homepage) {
		foreach my $box ('left_top','left_bottom','right_top','right_bottom'){
			my $box_type = $box."_type";
			$homepage{$box}{"type"} = $user_homepage->{$box_type};
			if ($homepage{$box}{"type"} == USER_HOMEPAGE_TYPE_SYSTEM_BROWSE && ( !$vars->{'per_field'} || $vars->{'per_field'} eq "") ){
				get_system_browse();
			} elsif ($homepage{$box}{"type"} == USER_HOMEPAGE_TYPE_USER_NEW_ISSUES && (!$vars->{'new_bugs'} || $vars->{'new_bugs'} eq "") ){
				$homepage{$box}{"bugs_list"} = $user->get_user_issues(USER_HOMEPAGE_TYPE_USER_NEW_ISSUES);	
				$homepage{$box}{"query"} = "buglist.cgi?query_format=advanced&emailassigned_to1=1&emailtype1=exact&email1=".$user->login."&bug_status=NEW";
				$homepage{$box}{"query_name"} = "New issues lists for user ".$user->name;
			} elsif ($homepage{$box}{"type"} == USER_HOMEPAGE_TYPE_USER_OPEN_ISSUES && (!$vars->{'open_bugs'} || $vars->{'open_bugs'} eq "") ){
				$homepage{$box}{"bugs_list"} = $user->get_user_issues(USER_HOMEPAGE_TYPE_USER_OPEN_ISSUES);
				$homepage{$box}{"query"} = "buglist.cgi?query_format=advanced&emailassigned_to1=1&emailtype1=exact&email1=".$user->login."&bug_status=ASSIGNED&bug_status=REOPENED";
				$homepage{$box}{"query_name"} = "Open issues lists for user ".$user->name;
			} elsif ($homepage{$box}{"type"} == USER_HOMEPAGE_TYPE_USER_SAVED_SEARCH) {
				$homepage{$box}{"bugs_list"} = $user->get_user_issues(USER_HOMEPAGE_TYPE_USER_SAVED_SEARCH,$user_homepage->{$box});
				$homepage{$box}{"query"} = "buglist.cgi?cmdtype=runnamed&amp;namedcmd=".$user_homepage->{$box};
				$homepage{$box}{"query_name"} = $user_homepage->{$box};
			}
			
		}
	}
	
	$vars->{'homepage'} = \%homepage;
} 

###############################################################################
# Main Body Execution
###############################################################################

# Generate and return the UI (HTML page) from the appropriate template.
$template->process("index.html.tmpl", $vars)
  || ThrowTemplateError($template->error());


###############################################################################
# Subrutines
###############################################################################
sub get_system_browse {
	my $selectable_products = $user->get_selectable_products;
	my @products = grep {$_->showonhomepage == 1} @$selectable_products;
	my @products_info;
	
	my $per_field = "NONE";
	my $per_field_name = "NONE";
	my $per_field_type = ""; 
	my $tv_field = new Bugzilla::Field ({'name' => 'cf_target_version'});
	if ($tv_field){
		$per_field = "cf_target_version";
		$per_field_name = "Target Version";
		$per_field_type = $tv_field->type;
	} elsif (Bugzilla->params->{'usetargetmilestone'}){
		$per_field = "target_milestone";
		$per_field_name = "Target Milestone";
	}
	
	foreach my $product (@products){
		# for backward compatability - support Target Version custom field
		if ($per_field eq "cf_target_version"){
			my $target_versions = $product->active_for_custom_versions();
			my @product_info;
			foreach my $tv (@$target_versions){
				my $tvname = $tv->name();
				my $tvcount = custom_bug_count($per_field_type,$product->id,$tvname,0);
				my $tvcounto = custom_bug_count($per_field_type,$product->id,$tvname,1);
				my %tv_info;
				$tv_info{'name'} = $tvname;
				$tv_info{'total'} = $tvcount;
				$tv_info{'opened'} = $tvcounto;
				push (@product_info,\%tv_info);
		
			}
			push (@products_info,{"name"=>$product->name, "info"=>\@product_info});
		} elsif (Bugzilla->params->{'usetargetmilestone'}){
			my $milestones = $product->visible_milestones();
			my @product_info;
			foreach my $m (@$milestones){
				my $mname = $m->name();
				my $mcount = $m->bug_count();
				my $mcounto = $m->bug_count_opened();
				my %m_info;
				$m_info{'name'} = $mname;
				$m_info{'total'} = $mcount;
				$m_info{'opened'} = $mcounto;
				push (@product_info,\%m_info);
		
			}
			push (@products_info,{"name"=>$product->name, "info"=>\@product_info});
		}
	}
	$vars->{'per_field'} = $per_field;
	$vars->{'per_field_name'} = $per_field_name;
	$vars->{'products_info'} = \@products_info;
}

sub custom_bug_count {
    my ($per_field_type,$product_id,$version,$opened) = @_;
    my $dbh = Bugzilla->dbh;
    
    my $custom_bug_count = 0;
    
    my $query = "SELECT COUNT(*) FROM ";
    if ($per_field_type == FIELD_TYPE_SINGLE_SELECT){
    	$query .= "bugs WHERE product_id = ? AND cf_target_version = ? ";
    } else {
    	$query .= "bug_cf_target_version bc JOIN bugs on (bc.bug_id = bugs.bug_id) WHERE bugs.product_id = ? AND bc.value = ?";
    }
    if ($opened){
    	$query .= " AND bug_status in ('NEW','ASSIGNED','REOPENED')",
    } 
    $custom_bug_count = $dbh->selectrow_array($query,undef, $product_id, $version);

    return $custom_bug_count;
}

