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
# Contributor(s): Terry Weissman <terry@mozilla.org>

use strict;

use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;
use Bugzilla::Error;
use Bugzilla::User;
use Bugzilla::Keyword;
use Bugzilla::Bug;
use Bugzilla::Menu;

my $cgi = Bugzilla->cgi;
my $template = Bugzilla->template;

my $user = Bugzilla->login();
my $vars = Bugzilla::Menu::PopulateClassificationAndProducts();

# Editable, 'single' HTML bugs are treated slightly specially in a few places
my $single = !$cgi->param('format')
  && (!$cgi->param('ctype') || $cgi->param('ctype') eq 'html');

# If we don't have an ID, _AND_ we're only doing a single bug, then prompt
if (!$cgi->param('id') && $single) {
    print Bugzilla->cgi->header();
    $template->process("bug/choose.html.tmpl", $vars) ||
      ThrowTemplateError($template->error());
    exit;
}

my $format = $template->get_format("bug/show", scalar $cgi->param('format'), 
                                   scalar $cgi->param('ctype'));

my @bugs = ();
my %marks;

# If the user isn't logged in, we use data from the shadow DB. If he plans
# to edit the bug(s), he will have to log in first, meaning that the data
# will be reloaded anyway, from the main DB.
Bugzilla->switch_to_shadow_db unless $user->id;

if ($single) {
    my $id = $cgi->param('id');
    push @bugs, Bugzilla::Bug->check($id);
    if (defined $cgi->param('mark')) {
        foreach my $range (split ',', $cgi->param('mark')) {
            if ($range =~ /^(\d+)-(\d+)$/) {
               foreach my $i ($1..$2) {
                   $marks{$i} = 1;
               }
            } elsif ($range =~ /^(\d+)$/) {
               $marks{$1} = 1;
            }
        }
    }
    # add viewvc_root for product
    my $product = new Bugzilla::Product($bugs[0]->product_id);
    $vars->{'viewvc_root'} = $product->viewvc_root if ($product->viewvc_root && $product->viewvc_root ne "");
    
	# check if custom template(s) exist
	my $base_t = "bug/edit";
	my $template_name = $base_t;
	
	my $bug_entity = $cgi->param('newentity') ? $cgi->param('newentity') : $bugs[0]->{'entity'};
	$vars->{'newentity'} = $cgi->param('newentity') ? $cgi->param('newentity') : "";
	
	my $byproduct = $base_t."-".$product->name;
	my $byentity = $base_t."-".$bug_entity;
	my $byboth = $base_t."-".$product->name."-".$bug_entity;
	
	if ($template->check_format($byboth)){
		$template_name = $byboth;
	} elsif (Bugzilla->params->{'templates_by'} eq "By Issue Type") {
		if ($template->check_format($byentity)){
			$template_name = $byentity;
		} elsif ($template->check_format($byproduct)){
			$template_name = $byproduct;
		}
	} else {
		if ($template->check_format($byproduct)){
			$template_name = $byproduct;
		} elsif ($template->check_format($byentity)){
			$template_name = $byentity;
		}
	}
	
	# prepare list of other templates by Issue Type
	my @templates_by_ent;
	my $special_cur_tmpl = ($template_name eq $byentity || $template_name eq $byboth) ? 1 : 0;
	foreach my $ent (@{Bugzilla::Entity::get_all_entities_values()}){
		my $templates_by_ent = 0;
		if ($special_cur_tmpl ||
			$template->check_format($base_t."-".$product->name."-".$ent) || 
			((Bugzilla->params->{'templates_by'} eq "By Issue Type") && ($template->check_format($base_t."-".$ent)))) {
			$templates_by_ent = 1;
		}
		push @templates_by_ent, { 
				'entity' => $ent, 
				'template_avail' => $templates_by_ent 
				};
	}
	$vars->{'templates_by_ent'} = \@templates_by_ent;
	
	$vars->{'edit_template_name'} = $template_name.".html.tmpl";
	
	# prepare email fields
	if (Bugzilla->params->{"use_send_email_link"}){
		my $comments = $bugs[0]->longdescs;
		my $body = "";
		my $counter = 0;
		foreach my $comment (@$comments){
			my $desc = $comment->{'body'};
			$desc =~ s/\r/ /g;
			
			if($counter == 0){
				$body = 'Description:\n\n';
				$body = $body. " ".  $desc;
				$body =~ s/\"/\'/g;
				$body =~ s/.\// /g;
				$body =~ s/\\[^\\n]/ /g;
				$body = $body . ' ';
		   } else {
				$body = $body. '\n\n------- Additional Comment #'. $counter. " From ". $comment->{'author'}->name. " ".  $comment->{'time'}. '\n'.$desc;
		   }
		
			$counter++;
		}
		
		my @personal = split(/\n/, $body);
		my $list = "";
		my $personal_counter = 0;
		foreach my $i (@personal) {
			if($personal_counter < 50){
				$list = $list. $i. '\n';
			}
			$personal_counter++;
		}
		
		# make the size of the body to a limit of 1120 bytes.
		my $list_size = length $list;
		while($list_size > 1120)	{
		    chop $list;
		    $list_size = length $list;
		}
		$list =~ s/\"/\'/g;
		$list =~ s/.\// /g;
		$list =~ s/\\[^\\n]/ /g;
		$list = $list . ' ';
		
		$vars->{'email_body'} = $list;
		
		
		my $email_short_desc = $bugs[0]->short_desc;
		$email_short_desc =~ s/\"/\'/g;
		$email_short_desc =~ s/.\// /g;
		$email_short_desc =~ s/\\[^\\n]/ /g;
		$vars->{'email_short_desc'} = $email_short_desc;
		
	}

} else {
    foreach my $id ($cgi->param('id')) {
        # Be kind enough and accept URLs of the form: id=1,2,3.
        my @ids = split(/,/, $id);
        foreach (@ids) {
            my $bug = new Bugzilla::Bug($_);
            # This is basically a backwards-compatibility hack from when
            # Bugzilla::Bug->new used to set 'NotPermitted' if you couldn't
            # see the bug.
            if (!$bug->{error} && !$user->can_see_bug($bug->bug_id)) {
                $bug->{error} = 'NotPermitted';
            }
            push(@bugs, $bug);
        }
    }
}

# Determine if Patch Viewer is installed, for Diff link
eval {
  require PatchReader;
  $vars->{'patchviewerinstalled'} = 1;
};

$vars->{'bugs'} = \@bugs;
$vars->{'marks'} = \%marks;
$vars->{'use_keywords'} = 1 if Bugzilla::Keyword::keyword_count();

my @bugids = map {$_->bug_id} grep {!$_->error} @bugs;
$vars->{'bugids'} = join(", ", @bugids);

# Next bug in list (if there is one)
my @bug_list;
if ($cgi->cookie("BUGLIST")) {
    @bug_list = split(/:/, $cgi->cookie("BUGLIST"));
}

$vars->{'bug_list'} = \@bug_list;

# Work out which fields we are displaying (currently XML only.)
# If no explicit list is defined, we show all fields. We then exclude any
# on the exclusion list. This is so you can say e.g. "Everything except 
# attachments" without listing almost all the fields.
my @fieldlist = (Bugzilla::Bug->fields, 'flag', 'group', 'long_desc', 
                 'attachment', 'attachmentdata', 'token');
my %displayfields;

if ($cgi->param("field")) {
    @fieldlist = $cgi->param("field");
}

unless (Bugzilla->user->in_group(Bugzilla->params->{"timetrackinggroup"})) {
    @fieldlist = grep($_ !~ /(^deadline|_time)$/, @fieldlist);
}

foreach (@fieldlist) {
    $displayfields{$_} = 1;
}

foreach ($cgi->param("excludefield")) {
    $displayfields{$_} = undef;    
}

$vars->{'displayfields'} = \%displayfields;

print $cgi->header($format->{'ctype'});

$template->process("$format->{'template'}", $vars)
  || ThrowTemplateError($template->error());
