#!/usr/bin/perl -wT
# -*- Mode: perl; indent-tabs-mode: nil -*-
#
##############################################################################
#
# editsubtasks.cgi
# -------------
#
##############################################################################

use strict;

use lib qw(. lib);

use Bugzilla ;
use Bugzilla::Error ;
use Bugzilla::Constants;
use Bugzilla::Entity;
use Bugzilla::Bug ;
use Bugzilla::Util ;
use Bugzilla::Menu;
use Bugzilla::Component;

local our $cgi = Bugzilla->cgi;
local our $template = Bugzilla->template;
local our $dbh = Bugzilla->dbh;

my $parent_id = $cgi->param('id');
my $user = Bugzilla->login(LOGIN_REQUIRED);
my $vars = Bugzilla::Menu::PopulateClassificationAndProducts();

################################################
# Subroutines
################################################

sub get_subtasks_list_from_db {

	my ($parent) = @_;

	my $subtasks_list = $parent->subtasks_list();
	# add fields to all subtasks coming from db
	foreach my $s (@$subtasks_list){
		$s->{'relevancy'} = "CHECKED";
		if ($s->{'bug_file_loc'} ne "")  {
			my @subb = split (/\\|\//,$s->{'bug_file_loc'});
			$s->{'bug_file_loc_cut'} = $subb[scalar(@subb) - 1];
		}
	}

	return @$subtasks_list;
}

sub get_subtasks_list{

	my @subtasks_list = ();
	my $index = trim($cgi->param('sub_index') || 0);
	for (my $i=1;$i<=$index;$i++){
		my $assigned_to = new Bugzilla::User(Bugzilla::User::login_to_id($cgi->param('assigned_to'.$i)));
		push @subtasks_list, {'index' => $i,
							  'relevancy' => ($cgi->param('relevancy'.$i) eq "on") ? "CHECKED":"",
							  'bug_id' => trim($cgi->param('bug_id'.$i) || ''),
							  'entity' => trim($cgi->param('entity'.$i) || ''),
							  'assigned_to' => $assigned_to,
							  'priority' => trim($cgi->param('priority'.$i) || ''),
							  'component' => trim($cgi->param('component'.$i) || ''),
							  'bug_status' => trim($cgi->param('bug_status'.$i) || ''),
							  'short_desc' => trim($cgi->param('short_desc'.$i) || ''),
							  'bug_file_loc' => trim($cgi->param('bug_file_loc'.$i) || ''),
							}
	}
	return @subtasks_list;
}

sub add_subtask {
	my ($parent,$entity) = @_;

	my $short_desc_prefix  = Bugzilla::Bug->get_subtask_prefix($entity,$parent->bug_id,$parent->short_desc());
	my $subtask = {'entity' => $entity,
		  		  'relevancy' => "CHECKED",
		  		  'short_desc_prefix' => $short_desc_prefix,
				  'bug_status' => 'NEW'};

	return $subtask;
}

sub add_template {

	my ($parent,$check_list) = @_;

	my $parent_entity = new Bugzilla::Entity({'name'  => $parent->entity});
	my @subtasks_template_list = split(/,/,$parent_entity->subtasks_list());
	my @subtasks_template;
	foreach my $sub_ent (@subtasks_template_list){
		if ($check_list){ # if there is a checklist, check if this subtask already defined
			if (lsearch($check_list, $sub_ent) < 0){
				my $subtask = add_subtask($parent,$sub_ent);
				push @subtasks_template, $subtask;
			}
		} else {
			my $subtask = add_subtask($parent,$sub_ent);
			push @subtasks_template, $subtask;
		}

	}

	return \@subtasks_template;
}

################################################
# Main
################################################

#
# often used variables
#
my $parent_bug_id = ($cgi->param('id') || '');
my $action = ($cgi->param('action') || '');
my @subtask_entities = Bugzilla::Entity->get_all_subtask_entities();
my $parent = new Bugzilla::Bug($parent_bug_id);
my @subtasks_list = get_subtasks_list();
if (@subtasks_list == 0){
	@subtasks_list = get_subtasks_list_from_db($parent);
}

#
$vars->{'parent'} = $parent;
$vars->{'subtask_entities'} = \@subtask_entities;
$vars->{'users'} = Bugzilla::User::get_userlist();
$vars->{'choices'} = $parent->choices();

$vars->{'title'} = "Edit Subtasks";


#
# no action: display subtasks list
#
if ($action eq ''){
	$vars->{'subtasks_template'} = add_template($parent);
	$vars->{'subtasks_list'} = \@subtasks_list ;
}

#
# add - add new subtask line
#
if ($action eq 'add'){

	my $add_ent = trim($cgi->param('subtask_entities')||'');
	my $subtask = add_subtask($parent,$add_ent);
	push @subtasks_list, $subtask;
	$vars->{'subtasks_list'} = \@subtasks_list;
}

#
# update - save changes to database
#
if ($action eq 'update'){

	my $timestamp = $dbh->selectrow_array(q{SELECT NOW()});
	my $sort_key = $cgi->param('sort_key') || 0;

	foreach my $sub (@subtasks_list){
		$dbh->bz_start_transaction();
		
		if ($sub->{'relevancy'} eq "CHECKED") {
			$sort_key ++;
			if (!$sub->{'bug_id'}) {
				# new subtask
				if (Bugzilla->params->{'mand_sub_sumprefix'}) {
					my $short_desc_prefix  = Bugzilla::Bug->get_subtask_prefix($sub->{'entity'},$parent->bug_id,$parent->short_desc());
			        if (index($sub->{'short_desc'},$short_desc_prefix) != 0) {
			        	$sub->{'short_desc'} = $short_desc_prefix.$sub->{'short_desc'};
					}
				}
				# copy relevant fields from parent
				my %parent_fields = $parent->get_parent_fields();
				my %issue_params = %parent_fields;

				foreach my $field ('entity','short_desc','priority','bug_file_loc','component') {
					$issue_params{$field} = $sub->{$field};
				}
				$issue_params{'assigned_to'} = $sub->{'assigned_to'}->login;
				$issue_params{'sort_key'} = $sort_key;
				$issue_params{'bug_status'} = "NEW";
				$issue_params{'parent_bug_id'} = $parent->bug_id;
				$issue_params{'everconfirmed'} = 1;
				$issue_params{'comment'}="+++ This issue was initially created as a subtask of Issue ".$parent->bug_id." +++";

				my $subtask = Bugzilla::Bug->create(\%issue_params);
			} 
		}
		
		$dbh->bz_commit_transaction();
    } # for

    @subtasks_list = get_subtasks_list_from_db($parent);
    $vars->{'subtasks_list'} = \@subtasks_list;

}

#
# attach - attach existing issue as a subtask
#
if ($action eq 'attach'){

	my $attach_to = trim($cgi->param('attach_to') || '');
	if ($attach_to eq ""){
		ThrowUserError("attach_invalid_issue_id");
	} else {
		# validation checks
		if ($attach_to == $parent->bug_id) {
            ThrowUserError("attach_of_self_disallowed");
        }
		my $attach = new Bugzilla::Bug($attach_to);
		if (!$attach){
			ThrowUserError("attach_invalid_issue_id");
		}
		if ($attach->has_subtasks()){
			ThrowUserError("attach_already_parent");
		}
		if ($attach->parent_bug_id ne "" && $attach->parent_bug_id ne "0"){
            ThrowUserError("attach_already_subtask");
        }
        if (!$attach->is_subtask) {
        	ThrowUserError("attach_not_subtask_entity");
        }
		# common fields
		my $ignore_common_valid = trim($cgi->param('ignore_common_valid') || "");
		if (Bugzilla->params->{'common_fields_for_subtasks'} && $ignore_common_valid ne "on") {
			if (Bugzilla->params->{'usetargetmilestone'}){
				if ($attach->product_id ne $parent->product_id || $attach->version ne $parent->version
					|| $attach->target_milestone ne $parent->target_milestone ) {
						ThrowUserError("attach_common_fields_not_identical");
				}
			} else {
				if ($attach->product_id ne $parent->product_id || $attach->version ne $parent->version) {
						ThrowUserError("attach_common_fields_not_identical");
				}
			}
		} 

		# attach as subtask new subtask
		$dbh->bz_start_transaction();
		$attach->attach_as_subtask($user->id,$parent);
		$dbh->bz_commit_transaction();
		# add it to the subtasks list
		push @subtasks_list , {'relevancy' => "CHECKED",
							  'bug_id' => $attach->{'bug_id'},
							  'entity' => $attach->{'entity'},
							  'assigned_to' => $attach->assigned_to,
							  'priority' => $attach->{'priority'},
							  'component' => $attach->component,
							  'bug_status' => $attach->{'bug_status'},
							  'short_desc' => $attach->short_desc,
							  'bug_file_loc' => $attach->{'bug_file_loc'},
							 };
    	$vars->{'subtasks_list'} = \@subtasks_list;
	}

}

#
# detach - detach subtask from its parent
#
if ($action eq 'detach'){
	my $detach_subtask = trim($cgi->param('detach_subtask') || '');
	my $detach = new Bugzilla::Bug($detach_subtask);
	$dbh->bz_start_transaction();
	$detach->detach_subtask($parent_bug_id);
	$dbh->bz_commit_transaction();
		
	@subtasks_list = get_subtasks_list_from_db($parent);
    $vars->{'subtasks_list'} = \@subtasks_list;
    $vars->{'new_message'} = get_text('detach_subtask', { subtask => $detach_subtask });
	
}

#
# add_template - add template if defined and if not added yet
#
if ($action eq 'add_template'){

	my @check_list;
	foreach my $sub(@subtasks_list){
		push @check_list,$sub->{'entity'};
	}

	my $subtasks_template = add_template($parent,\@check_list);
	push (@subtasks_list, @$subtasks_template);
	$vars->{'subtasks_list'} = \@subtasks_list ;

}

#
# sort_list - sort list of subtasks
#
if ($action eq "sort"){

	# if list is sorted, show it in the correct order
    my $sorted_sub_list = trim($cgi->param('sorted_sub_list') || '');
    if ($sorted_sub_list ne '') {
		my @list = split(/,/, $sorted_sub_list);
		my @subtasks_list_new;
		foreach my $ind (@list){
			push @subtasks_list_new, $subtasks_list[$ind-1];
		}
		$vars->{'subtasks_list'} = \@subtasks_list_new ;
    } else {
    	$vars->{'subtasks_list'} = \@subtasks_list ;
    }

}


  print $cgi->header();
  $template->process("subtasks/edit.html.tmpl", $vars)
      || ThrowTemplateError($template->error());


