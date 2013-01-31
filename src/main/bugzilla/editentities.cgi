#!/usr/bin/perl -wT
# -*- Mode: perl; indent-tabs-mode: nil; cperl-indent-level: 4 -*-


use strict;
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;
use Bugzilla::Util;
use Bugzilla::Error;
use Bugzilla::Entity;
use Bugzilla::Token;
use Bugzilla::Menu;

my $dbh = Bugzilla->dbh;
my $cgi = Bugzilla->cgi;
my $template = Bugzilla->template;

my $user = Bugzilla->login(LOGIN_REQUIRED);
my $vars = Bugzilla::Menu::PopulateClassificationAndProducts();

$user->in_group('admin')
  || ThrowUserError('auth_failure', {group  => 'admin',
                                     action => 'edit',
                                     object => 'entities'});


sub compute_fields_from_policy{
	my $subtask_policy = shift ;
	my $subtask_allowed ;
	my $is_subtask ;
	my $subtask_only;
	if ($subtask_policy == 0 ) {
			$subtask_allowed = 0;
			$is_subtask = 0;
			$subtask_only = 0;
		} elsif ($subtask_policy == 1) {
			$subtask_allowed = 1;
			$is_subtask = 1;
			$subtask_only = 0;
		} elsif ($subtask_policy == 2) {
			$subtask_allowed = 1;
			$is_subtask = 0;
			$subtask_only = 0;
		} elsif ($subtask_policy == 3) {
			$subtask_allowed = 0;
			$is_subtask = 1;
			$subtask_only = 1;
		}
		return ($subtask_allowed , $is_subtask, $subtask_only)
}

sub check_subtasks_params {
	my ($subtask_policy,$subtasks_list) = @_;

	if ((($subtask_policy == 0)||($subtask_policy == 3)) && ($subtasks_list ne "")){
        ThrowUserError("not_parent_entity");
	}

	my @list = split(/,/, $subtasks_list);
	foreach my $ent (@list){
		 my $entity = new Bugzilla::Entity({'name' => $ent});
		if (!$entity){
			ThrowUserError("entity_does_not_exist",{ name => $ent });
		}
		if (!$entity->is_subtask()){
			ThrowUserError("entity_is_not_subtask",{ name => $ent });
		}
	}
}

print $cgi->header();

ThrowUserError("auth_entity_not_enabled") unless 1 ;

#
# often used variables
#
my $action	= trim($cgi->param('action') || '');
my $entity_name	= trim($cgi->param('entity_name') || '');
my $token   = $cgi->param('token');

$vars->{'policies'} = Bugzilla::Entity::GetPolicies();
my @sub_entities = Bugzilla::Entity::get_all_subtask_entities();
$vars->{'sub_entities'} = \@sub_entities;

#
# action='' -> Show nice list of entities
#
unless ($action) {
	
	my @all_entities = Bugzilla::Entity::get_all_entities();
	$vars->{'entities'} = \@all_entities;
	
    $template->process("admin/entities/list.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

#
# action='add' -> present form for parameters for new entity
#
# (next action will be 'new')
#

if ($action eq 'add') {

    $vars->{'token'} = issue_session_token('add_entity');
    $template->process("admin/entities/create.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

#
# action='new' -> add entity entered in the 'action=add' screen
#

if ($action eq 'new') {
    check_token_data($token, 'add_entity');

    my $sortkey = trim($cgi->param('sortkey') || 0);

	my $default_entity = $cgi->param('default_entity') ? 1 : 0;
	#subtasks params
	my $subtask_policy = $cgi->param('subtask_policy') || 0;
	my $subtask_valid = $cgi->param('subtask_valid') ? 1 : 0;
	my $subtasks_list = trim($cgi->param('subtasks_list') || "");
	check_subtasks_params($subtask_policy,$subtasks_list);
	my ($subtask_allowed, $is_subtask, $subtask_only) = compute_fields_from_policy($subtask_policy) ;
	
	my $entity =
      Bugzilla::Entity->create({ value				=> $entity_name,
      							 sortkey			=> $sortkey,
                                 default_entity		=> $default_entity,
                                 is_subtask 		=> $is_subtask,
                                 subtask_allowed	=> $subtask_allowed,
                                 subtask_only		=> $subtask_only,
                                 subtask_valid		=> $subtask_valid,
                                 subtasks_list		=> $subtasks_list });
                                 
    $vars->{'message'} = 'entity_created';
    $vars->{'entity'} = $entity;
    
    delete_token($token);
    
    my @all_entities = Bugzilla::Entity::get_all_entities();
    $vars->{'entities'} = \@all_entities;

    $template->process("admin/entities/list.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;

}

#
# action='del' -> ask if user really wants to delete
#
# (next action would be 'delete')
#

if ($action eq 'del') {

    my $entity = Bugzilla::Entity::check_entity($entity_name);

    if ($entity->default_entity == 1) {
        ThrowUserError("entity_not_deletable");
    }
    if ($entity->bug_count > 0){
    	delete_token($token);
    }else{
    	$vars->{'token'} = issue_session_token('delete_entity');
    }
    $vars->{'entity'} = $entity;

    $template->process("admin/entities/confirm-delete.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

#
# action='delete' -> really delete the entity
#
if ($action eq 'delete') {
    check_token_data($token, 'delete_entity');

    my $entity = Bugzilla::Entity::check_entity($entity_name);

    if ($entity->default_entity == 1) {
        ThrowUserError("entity_not_deletable");
    }
    
    $entity->remove_from_db;

    $vars->{'message'} = 'entity_deleted';
    $vars->{'entity'} = $entity;
    delete_token($token);
    
    my @all_entities = Bugzilla::Entity::get_all_entities();
    $vars->{'entities'} = \@all_entities;

    $template->process("admin/entities/list.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

#
# action='edit' -> present the edit entity form
#
# (next action would be 'update')
#

if ($action eq 'edit') {

	$vars->{'entity'} = Bugzilla::Entity::check_entity($entity_name);;
    $vars->{'token'} = issue_session_token('edit_entity');

    $template->process("admin/entities/edit.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}

#
# action='update' -> update the entity
#
if ($action eq 'update') {
    check_token_data($token, 'edit_entity');

    my $entity_old_name = trim($cgi->param('entityold') || '');
    my $entity = Bugzilla::Entity->check({name => $entity_old_name});

    my $sortkey = trim($cgi->param('sortkey') || 0);
	my $default_entity = $cgi->param('default_entity') ? 1 : 0;;
	# subtasks params
	my $subtask_policy = $cgi->param('subtask_policy') || 0;
	my $subtask_valid = $cgi->param('subtask_valid') ? 1 : 0;;
    my $subtasks_list = trim($cgi->param('subtasks_list') || "");
    check_subtasks_params($subtask_policy,$subtasks_list);
    my ($subtask_allowed,$is_subtask,$subtask_only) = compute_fields_from_policy($cgi->param('subtask_policy')) ;
    
    $entity->set_value($entity_name);
    $entity->set_sortkey($sortkey);
    $entity->set_default_entity($default_entity);
    $entity->set_subtask_allowed($subtask_allowed);
    $entity->set_is_subtask($is_subtask);
    $entity->set_subtask_only($subtask_only);
    $entity->set_subtask_valid($subtask_valid);
    $entity->set_subtasks_list($subtasks_list);
	my $changes = $entity->update();

    $vars->{'message'} = 'entity_updated';
    $vars->{'entity'} = $entity;
    $vars->{'changes'} = $changes;
    delete_token($token);
    
    my @all_entities = Bugzilla::Entity::get_all_entities();
    $vars->{'entities'} = \@all_entities;

    $template->process("admin/entities/list.html.tmpl", $vars)
      || ThrowTemplateError($template->error());
    exit;
}
    

#
# No valid action found
#

ThrowCodeError("action_unrecognized", {action => $action});
