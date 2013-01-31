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
#                 Dan Mosedale <dmose@mozilla.org>
#                 Joe Robins <jmrobins@tgix.com>
#                 Gervase Markham <gerv@gerv.net>
#                 Marc Schumann <wurblzap@gmail.com>

use strict;
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Attachment;
use Bugzilla::BugMail;
use Bugzilla::Constants;
use Bugzilla::Util;
use Bugzilla::Error;
use Bugzilla::Bug;
use Bugzilla::User;
use Bugzilla::Field;
use Bugzilla::Hook;
use Bugzilla::Product;
use Bugzilla::Component;
use Bugzilla::Keyword;
use Bugzilla::Token;
use Bugzilla::Flag;
use Bugzilla::Menu;

my $user = Bugzilla->login(LOGIN_REQUIRED);

my $cgi = Bugzilla->cgi;
my $dbh = Bugzilla->dbh;
my $template = Bugzilla->template;
my $vars = Bugzilla::Menu::PopulateClassificationAndProducts();

######################################################################
# Main Script
######################################################################

# redirect to enter_bug if no field is passed.
print $cgi->redirect(correct_urlbase() . 'enter_bug.cgi') unless $cgi->param();

# Detect if the user already used the same form to submit a bug
my $token = trim($cgi->param('token'));
if ($token) {
    my ($creator_id, $date, $old_bug_id) = Bugzilla::Token::GetTokenData($token);
    unless ($creator_id
              && ($creator_id == $user->id)
              && ($old_bug_id =~ "^createbug:"))
    {
        # The token is invalid.
        ThrowUserError('token_does_not_exist');
    }

    $old_bug_id =~ s/^createbug://;

    if ($old_bug_id && (!$cgi->param('ignore_token')
                        || ($cgi->param('ignore_token') != $old_bug_id)))
    {
        $vars->{'bugid'} = $old_bug_id;
        $vars->{'allow_override'} = defined $cgi->param('ignore_token') ? 0 : 1;

        print $cgi->header();
        $template->process("bug/create/confirm-create-dupe.html.tmpl", $vars)
           || ThrowTemplateError($template->error());
        exit;
    }
}    

# fix @ chars in cc list
my $cc = $cgi->param('cc');
$cc =~ s/&#64;/@/g; 
$cgi->param('cc', $cc);

# do a match on the fields if applicable

&Bugzilla::User::match_field ($cgi, {
    'cc'            => { 'type' => 'multi'  },
    'assigned_to'   => { 'type' => 'single' },
    'qa_contact'    => { 'type' => 'single' },
    '^requestee_type-(\d+)$' => { 'type' => 'multi' },
});

if (defined $cgi->param('maketemplate')) {
    $vars->{'url'} = $cgi->canonicalise_query('token');
    $vars->{'short_desc'} = $cgi->param('short_desc');
    
    print $cgi->header();
    $template->process("bug/create/make-template.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

umask 0;

# get current time
my $timestamp = $dbh->selectrow_array(q{SELECT NOW()});

# Group Validation
my @selected_groups;
foreach my $group (grep(/^bit-\d+$/, $cgi->param())) {
    $group =~ /^bit-(\d+)$/;
    push(@selected_groups, $1);
}

# The format of the initial comment can be structured by adding fields to the
# enter_bug template and then referencing them in the comment template.
my $comment;
my $format = $template->get_format("bug/create/comment",
                                   scalar($cgi->param('format')), "txt");
$template->process($format->{'template'}, $vars, \$comment)
    || ThrowTemplateError($template->error());

# Include custom fields editable on bug creation.
my @custom_bug_fields = grep {$_->type != FIELD_TYPE_MULTI_SELECT && $_->enter_bug}
                             Bugzilla->active_custom_fields;

# Undefined custom fields are ignored to ensure they will get their default
# value (e.g. "---" for custom single select fields).
my @bug_fields = grep { defined $cgi->param($_->name) } @custom_bug_fields;
@bug_fields = map { $_->name } @bug_fields;

push(@bug_fields, qw(
    product
    component
	entity

    assigned_to
    qa_contact

    alias
    blocked
    commentprivacy
    bug_file_loc
    bug_severity
    bug_status
    dependson
    keywords
    short_desc
    op_sys
    priority
    rep_platform
    version
    target_milestone
    status_whiteboard

    estimated_time
    deadline
    crm_list
));

my %bug_params;
foreach my $field (@bug_fields) {
    $bug_params{$field} = $cgi->param($field);
}
$bug_params{'creation_ts'} = $timestamp;
$bug_params{'cc'}          = [$cgi->param('cc')];
$bug_params{'groups'}      = \@selected_groups;
$bug_params{'comment'}     = $comment;

my @multi_selects = grep {$_->type == FIELD_TYPE_MULTI_SELECT && $_->enter_bug}
                         Bugzilla->active_custom_fields;

foreach my $field (@multi_selects) {
    $bug_params{$field->name} = [$cgi->param($field->name)];
}

my $bug = Bugzilla::Bug->create(\%bug_params);

# Get the bug ID back.
my $id = $bug->bug_id;

# Set Version cookie, but only if the user actually selected
# a version on the page.
if (defined $cgi->param('version')) {
    $cgi->send_cookie(-name => "VERSION-" . $bug->product,
                      -value => $bug->version,
                      -expires => "Fri, 01-Jan-2038 00:00:00 GMT");
}

# We don't have to check if the user can see the bug, because a user filing
# a bug can always see it. You can't change reporter_accessible until
# after the bug is filed.

# Attach to another issue if requested
my $attach_to = trim($cgi->param('attach_to') || '');
if ($attach_to ne "")  {
	my $attach_parent = new Bugzilla::Bug($attach_to);
	# validations
	my $valid = 1;
	my $error = "";
	if (!$attach_parent){
		$error = 'attach_invalid_issue_id';
		$valid = 0;
	} elsif (!$attach_parent->subtask_allowed){
		$error = 'attach_not_parent_entity';
		$valid = 0;
	} elsif ($attach_parent->parent_bug_id ne "" && $attach_parent->parent_bug_id ne "0"){
        $error = 'attach_already_subtask';
        $valid = 0;
    }
    # common fields
	my $ignore_common_valid = trim($cgi->param('ignore_common_valid') || "");
	if (Bugzilla->params->{'common_fields_for_subtasks'} && $ignore_common_valid ne "on") {
		if (Bugzilla->params->{'usetargetmilestone'}){
			if ($attach_parent->product_id ne $bug->product_id || $attach_parent->version ne $bug->version
				|| $attach_parent->target_milestone ne $bug->target_milestone ) {
					$error = 'attach_common_fields_not_identical';
					$valid = 0;
			}
		} else {
			if ($attach_parent->product_id ne $bug->product_id || $attach_parent->version ne $bug->version) {
					$error = 'attach_common_fields_not_identical';
					$valid = 0;
			}
		}
	} 
	
	if ($valid){
		# attach as subtask 
		$dbh->bz_start_transaction();
		$bug->attach_as_subtask($user->id,$attach_parent);
		$dbh->bz_commit_transaction();
	} else {
		$vars->{'message'} = 'attach_as_subtask_failed';
		my $message2;
		$vars->{error} = $error;
		$vars->{only_error_message} = 1;
        $template->process("global/user-error.html.tmpl", $vars, \$message2) || ThrowTemplateError($template->error());
		$vars->{'message2'} = $message2;
		$vars->{'parent'} = $attach_to;
	}
	
}

# Add an attachment if requested.
if (defined($cgi->upload('data')) || $cgi->param('attachurl')) {
    $cgi->param('isprivate', $cgi->param('commentprivacy'));
    my $attachment = Bugzilla::Attachment->create(!THROW_ERROR,
                                                  $bug, $user, $timestamp, $vars);

    if ($attachment) {
        # Update the comment to include the new attachment ID.
        # This string is hardcoded here because Template::quoteUrls()
        # expects to find this exact string.
        my $new_comment = "Created an attachment (id=" . $attachment->id . ")\n" .
                          $attachment->description . "\n";
        # We can use $bug->longdescs here because we are sure that the bug
        # description is of type CMT_NORMAL. No need to include it if it's
        # empty, though.
        if ($bug->longdescs->[0]->{'body'} !~ /^\s+$/) {
            $new_comment .= "\n" . $bug->longdescs->[0]->{'body'};
        }
        $bug->update_comment($bug->longdescs->[0]->{'id'}, $new_comment);
    }
    else {
        $vars->{'message'} = 'attachment_creation_failed';
    }

    # Determine if Patch Viewer is installed, for Diff link
    eval {
        require PatchReader;
        $vars->{'patchviewerinstalled'} = 1;
    };
}

# Add flags, if any. To avoid dying if something goes wrong
# while processing flags, we will eval() flag validation.
# This requires errors to die().
# XXX: this can go away as soon as flag validation is able to
#      fail without dying.
my $error_mode_cache = Bugzilla->error_mode;
Bugzilla->error_mode(ERROR_MODE_DIE);
eval {
    Bugzilla::Flag::validate($id, undef, SKIP_REQUESTEE_ON_ERROR);
    Bugzilla::Flag->process($bug, undef, $timestamp, $vars);
};
Bugzilla->error_mode($error_mode_cache);
if ($@) {
    $vars->{'message'} = 'flag_creation_failed';
    $vars->{'flag_creation_error'} = $@;
}

# Email everyone the details of the new bug 
$vars->{'mailrecipients'} = {'changer' => $user->login};

$vars->{'id'} = $id;
$vars->{'bug'} = $bug;

Bugzilla::Hook::process("post_bug-after_creation", { vars => $vars });

ThrowCodeError("bug_error", { bug => $bug }) if $bug->error;

$vars->{'sentmail'} = [];

push (@{$vars->{'sentmail'}}, { type => 'created',
                                id => $id,
                              });

foreach my $i (@{$bug->dependson || []}, @{$bug->blocked || []}) {
    push (@{$vars->{'sentmail'}}, { type => 'dep', id => $i, });
}

my @bug_list;
if ($cgi->cookie("BUGLIST")) {
    @bug_list = split(/:/, $cgi->cookie("BUGLIST"));
}
$vars->{'bug_list'} = \@bug_list;
$vars->{'use_keywords'} = 1 if Bugzilla::Keyword::keyword_count();

# add viewvc_root for product
my $product = new Bugzilla::Product($bug->product_id);
$vars->{'viewvc_root'} = $product->viewvc_root if ($product->viewvc_root && $product->viewvc_root ne "");

# check if custom template(s) exist
my $base_t = "bug/edit";
my $template_name = $base_t;

my $bug_entity = $cgi->param('newentity') ? $cgi->param('newentity') : $bug->{'entity'};
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
		
if ($token) {
    trick_taint($token);
    $dbh->do('UPDATE tokens SET eventdata = ? WHERE token = ?', undef, 
             ("createbug:$id", $token));
}

if (Bugzilla->usage_mode == USAGE_MODE_EMAIL) {
    Bugzilla::BugMail::Send($id, $vars->{'mailrecipients'});
    print $id;
}
else {
    print $cgi->header();
    $template->process("bug/create/created.html.tmpl", $vars)
        || ThrowTemplateError($template->error());
}

1;
