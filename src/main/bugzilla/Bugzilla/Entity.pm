# -*- Mode: perl; indent-tabs-mode: nil -*-
#

use strict;

package Bugzilla::Entity;

use Bugzilla::Util;
use Bugzilla::Error;
use Bugzilla::Product;
use Bugzilla::Constants;

# Currently, we only implement enough of the Bugzilla::Field::Choice
# interface to control the visibility of other fields.
use base qw(Bugzilla::Field::Choice);

###############################
####    Initialization     ####
###############################

use constant DB_TABLE => 'entity';

use constant NAME_FIELD => 'value';
use constant LIST_ORDER => 'sortkey, value';

use constant DB_COLUMNS => qw(
    id
    value
    sortkey
    default_entity
    subtask_allowed
    is_subtask
    subtask_only
    subtask_valid
    subtasks_list
);

our $columns = join(", ", DB_COLUMNS);

use constant REQUIRED_CREATE_FIELDS => qw(
    value
);

use constant UPDATE_COLUMNS => qw(
    value
    sortkey
    default_entity
    subtask_allowed
    is_subtask
    subtask_only
    subtask_valid
    subtasks_list
);

use constant VALIDATORS => {
    value   => \&_check_value,
    sort_key => \&_check_sort_key,
};

#####################################
# Implement Bugzilla::Field::Choice #
#####################################

sub field {
    my $invocant = shift;
    my $class = ref $invocant || $invocant;
    my $cache = Bugzilla->request_cache;
    $cache->{"field_$class"} ||= new Bugzilla::Field({ name => 'entity' });
    return $cache->{"field_$class"};
}

use constant is_default => 0;

###############################
####       Methods         ####
###############################


sub create {
    my $class = shift;
    my $dbh = Bugzilla->dbh;

    $dbh->bz_start_transaction();

    $class->check_required_create_fields(@_);
    my $params = $class->run_create_validators(@_);
    
    my $entity = $class->insert_create_data($params);
    
    my $default_entity = $entity->{'default_entity'};
    if ($default_entity){
    	reset_default_entity($entity->value);
    }

    $dbh->bz_commit_transaction();
    return $entity;
}

sub update {
	my $self = shift;
    my $changes = $self->SUPER::update(@_);

    # set default entity if set to yes
    if ($changes->{default_entity}){
    	reset_default_entity($self->value);
    }
    return $changes;
}

# Reset default entity for all entities except the input one
sub reset_default_entity {
	my ($new_default_ent_value) = @_;
	
	my $dbh = Bugzilla->dbh;
	
	$dbh->do("UPDATE entity set default_entity=0 where value!=?",undef,$new_default_ent_value);
}

sub get_legal_values {
	my $self = shift;
    my $issue_types = shift;

   	my @values;
   	if ($issue_types){
   		if ($issue_types == ISSUE_TYPES_REGULAR){
    		@values = Bugzilla::Entity->get_all_regular_entities();
    	} elsif ($issue_types == ISSUE_TYPES_SUBTASK){
    		@values = Bugzilla::Entity->get_all_subtask_entities();
    	} elsif ($issue_types == ISSUE_TYPES_PARENT){
 			@values = Bugzilla::Entity->get_all_parent_entities();
    	} else {
    		@values = Bugzilla::Entity->get_all_entities();
   		}
    } else {
    	@values = Bugzilla::Entity->get_all_entities();
   	}
    return @values;
}


################################
# Validators
################################

sub _check_value {
    my ($invocant, $value) = @_;

    $value = trim($value);
    $value || ThrowUserError('entity_not_specified');

    if (length($value) > MAX_ENTITY_SIZE) {
        ThrowUserError('entity_not_specified', {'name' => $value});
    }

    my $entity = new Bugzilla::Entity({'name' => $value});
    if ($entity && (!ref $invocant || $entity->id != $invocant->id)) {
        ThrowUserError('entity_already_exists', {'name' => $entity->value});
    }
    return $value;
}

sub _check_sort_key {
    my ($invocant, $sortkey) = @_;

    $sortkey = trim($sortkey);
    my $stored_sortkey = $sortkey;
    detaint_natural($sortkey)
      || ThrowUserError('field_invalid_sortkey', {'sortkey' => $stored_sortkey});
    
}

###############################
####      Accessors        ####
###############################

sub id          { return $_[0]->{'id'}; }
sub value       { return $_[0]->{'value'}; }
sub name   	    { return $_[0]->{'value'}; }
sub sortkey     { return $_[0]->{'sortkey'}; }

sub default_entity { return $_[0]->{'default_entity'};     }
sub subtask_allowed { return $_[0]->{'subtask_allowed'};     }
sub is_subtask { return $_[0]->{'is_subtask'};     }
sub subtask_only { return $_[0]->{'subtask_only'};     }
sub subtask_valid { return $_[0]->{'subtask_valid'};     }
sub subtasks_list { return $_[0]->{'subtasks_list'};     }
sub subtask_policy_name{ return GetSubPolicyName($_[0]->subtask_policy) ;}

###############################
####      Subroutines      ####
###############################

sub set_value { $_[0]->set('value', $_[1]); }
sub set_sortkey { $_[0]->set('sortkey', $_[1]); }
sub set_default_entity { $_[0]->set('default_entity', $_[1]); }
sub set_subtask_allowed { $_[0]->set('subtask_allowed', $_[1]); }
sub set_is_subtask { $_[0]->set('is_subtask', $_[1]); }
sub set_subtask_only { $_[0]->set('subtask_only', $_[1]); }
sub set_subtask_valid { $_[0]->set('subtask_valid', $_[1]); }
sub set_subtasks_list { $_[0]->set('subtasks_list', $_[1]); }

sub get_all_entities {
    my $dbh = Bugzilla->dbh;

    my $ids = $dbh->selectcol_arrayref(q{
        SELECT id FROM entity ORDER BY sortkey, value});

    my @entities;
    foreach my $id (@$ids) {
        push @entities, new Bugzilla::Entity($id);
    }
    return @entities;
}

sub get_all_entities_values {
    my $dbh = Bugzilla->dbh;

    my $values = $dbh->selectcol_arrayref(q{
        SELECT value FROM entity ORDER BY sortkey, value});

    return $values;
}

sub get_all_subtask_entities {
    my $dbh = Bugzilla->dbh;

    my $ids = $dbh->selectcol_arrayref(q{
        SELECT id FROM entity WHERE is_subtask=1 ORDER BY sortkey, value});

    my @entities;
    foreach my $id (@$ids) {
        push @entities, new Bugzilla::Entity($id);
    }
    return @entities;
}

sub get_all_subtask_entities_values {
    my $dbh = Bugzilla->dbh;

    my $values = $dbh->selectcol_arrayref(q{
        SELECT value FROM entity WHERE is_subtask=1 ORDER BY sortkey, value});

    return $values;
}

sub get_all_parent_entities {
    my $dbh = Bugzilla->dbh;

    my $ids = $dbh->selectcol_arrayref(q{
        SELECT id FROM entity WHERE subtask_allowed=1 ORDER BY sortkey, value});

    my @entities;
    foreach my $id (@$ids) {
        push @entities, new Bugzilla::Entity($id);
    }
    return @entities;
}

sub get_all_parent_entities_values {
    my $dbh = Bugzilla->dbh;

    my $values = $dbh->selectcol_arrayref(q{
        SELECT value FROM entity WHERE subtask_allowed=1 ORDER BY sortkey, value});

    return $values;
}

sub get_all_regular_entities {
    my $dbh = Bugzilla->dbh;

    my $ids = $dbh->selectcol_arrayref(q{
        SELECT id FROM entity WHERE subtask_only = 0 ORDER BY sortkey, value});

    my @entities;
    foreach my $id (@$ids) {
        push @entities, new Bugzilla::Entity($id);
    }
    return @entities;
}

sub get_all_regular_entities_values {
    my $dbh = Bugzilla->dbh;

    my $values = $dbh->selectcol_arrayref(q{
        SELECT value FROM entity WHERE subtask_only = 0 ORDER BY sortkey, value});

    return $values;
}

sub get_default_entity {
	my $dbh = Bugzilla->dbh;
	
	my $def_ent = $dbh->selectrow_array ("SELECT value from entity WHERE default_entity=1");
	return $def_ent;
}

sub check_entity {
    my ($value) = @_;

    unless ($value) {
        ThrowUserError("entity_not_specified");
    }

    my $entity = new Bugzilla::Entity({'name' => $value});

    unless ($entity) {
        ThrowUserError("entity_does_not_exist",
                       { name => $value });
    }

    return $entity;
}

sub bug_count {
    my $self = shift;
    my $dbh = Bugzilla->dbh;

    if (!defined $self->{'bug_count'}) {
        $self->{'bug_count'} = $dbh->selectrow_array(q{
            SELECT COUNT(*) FROM bugs
            WHERE entity = ?}, undef, $self->value) || 0;
    }
    return $self->{'bug_count'};
}

# Compute subtask policy from the db fields
sub subtask_policy {
	my $self = shift;
	
	my $subtask_policy = 0; #no parent , no subtask
	if (($self->subtask_allowed == 1)&&($self->is_subtask == 1)){
		$subtask_policy = 1; #both parent and subtask
	}
	if (($self->subtask_allowed == 1)&&($self->is_subtask == 0)){
		$subtask_policy = 2; # parent only
	}
	if ($self->subtask_only == 1){
		$subtask_policy = 3; # subtask only
	}
	return $subtask_policy;
}

sub GetSubPolicyName {

	my ($sub_policy) = @_;

	use Switch;
	switch ($sub_policy) {
		case 0	{ return "Can not be parent or no subtask issue"; }
		case 1	{ return "Can be both parent and subtask issue"; }
		case 2 	{ return "Can be parent issue only"; }
		case 3	{ return "Can be subtask issue only"; }
	}
	return undef ;
}

sub GetPolicies {
	my @policies = ({'i' => 0, 'name' => GetSubPolicyName(0)},
					{'i' => 1, 'name' => GetSubPolicyName(1)},
					{'i' => 2, 'name' => GetSubPolicyName(2)},
					{'i' => 3, 'name' => GetSubPolicyName(3)});

	return \@policies ;
}

#sub SetSubtaskPolicy($$$){
#
#	my ($subtask_allowed,$is_subtask,$subtask_only) = @_;
#
#	my $subtask_policy = 0; #no parent , no subtask
#	if (($subtask_allowed == 1)&&($is_subtask == 1)){
#		$subtask_policy = 1; #both parent and subtask
#	}
#	if (($subtask_allowed == 1)&&($is_subtask == 0)){
#		$subtask_policy = 2; # parent only
#	}
#	if ($subtask_only == 1){
#		$subtask_policy = 3; # subtask only
#	}

1;