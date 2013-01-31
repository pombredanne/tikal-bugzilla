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
# Contributor(s): Tiago R. Mello <timello@async.com.br>
#                 Max Kanat-Alexander <mkanat@bugzilla.org>

use strict;

package Bugzilla::Version;

use Bugzilla::Install::Util qw(vers_cmp);
use Bugzilla::Util;
use Bugzilla::Error;
use Bugzilla::Constants;

# Currently, we only implement enough of the Bugzilla::Field::Choice
# interface to control the visibility of other fields.
use base qw(Bugzilla::Field::Choice);

################################
#####   Initialization     #####
################################

use constant DEFAULT_VERSION => 'unspecified';

use constant DEFAULT_SORTKEY => 0;

use constant DB_TABLE => 'versions';

use constant DB_COLUMNS => qw(
    id
    value
    product_id
    status
    sortkey
);

use constant NAME_FIELD => 'value';
use constant LIST_ORDER => 'sortkey, value';

use constant REQUIRED_CREATE_FIELDS => qw(
    name
    product
    status
);

use constant UPDATE_COLUMNS => qw(
    value
    status
    sortkey
);

use constant VALIDATORS => {
    product => \&_check_product,
    sortkey => \&_check_sortkey,
    status => \&_check_status,
};

use constant UPDATE_VALIDATORS => {
    value => \&_check_value,
};

################################
# Validators
################################

sub _check_value {
    my ($invocant, $name, $product) = @_;

    $name = trim($name);
    $name || ThrowUserError('version_blank_name');
    if (length($name) > MAX_VERSION_SIZE) {
        ThrowUserError('version_name_too_long', {name => $name});
    }

    $product = $invocant->product if (ref $invocant);
    my $version = new Bugzilla::Version({product => $product, name => $name});
    if ($version && (!ref $invocant || $version->id != $invocant->id)) {
        ThrowUserError('version_already_exists', { name    => $version->name,
                                                   product => $product->name });
    }
    return $name;
}

sub _check_sortkey {
    my ($invocant, $sortkey) = @_;

    # Keep a copy in case detaint_signed() clears the sortkey
    my $stored_sortkey = $sortkey;

    if (!detaint_signed($sortkey) || $sortkey < MIN_SMALLINT || $sortkey > MAX_SMALLINT) {
        ThrowUserError('version_sortkey_invalid', {sortkey => $stored_sortkey});
    }
    return $sortkey;
}

sub _check_status {
	my ($invocant, $status) = @_;
	
	if ($status != VERSION_STATUS_UNRELEASED && $status != VERSION_STATUS_RELEASED 
		&& $status != VERSION_STATUS_FINAL && $status != VERSION_STATUS_ARCHIVED){
			ThrowUserError('version_status_invalid', {status => $status});
		}
	
	return $status;
}

sub _check_product {
    my ($invocant, $product) = @_;
    return Bugzilla->user->check_can_admin_product($product->name);
}

#####################################
# Implement Bugzilla::Field::Choice #
#####################################

sub field {
    my $invocant = shift;
    my $class = ref $invocant || $invocant;
    my $cache = Bugzilla->request_cache;
    $cache->{"field_$class"} ||= new Bugzilla::Field({ name => 'version' });
    return $cache->{"field_$class"};
}

use constant is_default => 0;

###############################

sub new {
    my $class = shift;
    my $param = shift;
    my $dbh = Bugzilla->dbh;

    my $product;
    if (ref $param) {
        $product = $param->{product};
        my $name = $param->{name};
        if (!defined $product) {
            ThrowCodeError('bad_arg',
                {argument => 'product',
                 function => "${class}::new"});
        }
        if (!defined $name) {
            ThrowCodeError('bad_arg',
                {argument => 'name',
                 function => "${class}::new"});
        }

        my $condition = 'product_id = ? AND value = ?';
        my @values = ($product->id, $name);
        $param = { condition => $condition, values => \@values };
    }

    unshift @_, $param;
    return $class->SUPER::new(@_);
}

sub new_from_list {
    my $self = shift;
    my $list = $self->SUPER::new_from_list(@_);
    #return [sort { vers_cmp(lc($a->name), lc($b->name)) } @$list];
    return $list;
}

sub bug_count {
    my $self = shift;
    my $dbh = Bugzilla->dbh;

    if (!defined $self->{'bug_count'}) {
        $self->{'bug_count'} = $dbh->selectrow_array(qq{
            SELECT COUNT(*) FROM bugs
            WHERE product_id = ? AND version = ?}, undef,
            ($self->product_id, $self->name)) || 0;
    }
    return $self->{'bug_count'};
}

sub remove_from_db {
    my $self = shift;
    my $dbh = Bugzilla->dbh;

    # The version cannot be removed if there are bugs
    # associated with it.
    if ($self->bug_count) {
        ThrowUserError("version_has_bugs", { nb => $self->bug_count });
    }

    $dbh->do(q{DELETE FROM versions WHERE product_id = ? AND value = ?},
              undef, ($self->product_id, $self->name));
}

sub update {
    my $self = shift;
    my ($name, $product, $status, $sortkey) = @_;
    my $dbh = Bugzilla->dbh;

    $name || ThrowUserError('version_not_specified');

    # Remove unprintable characters
    $name = clean_text($name);

    return 0 if (($name eq $self->name) && ($status eq $self->status) && ($sortkey eq $self->sortkey));
    my $version = new Bugzilla::Version({ product => $product, name => $name });
    
    if ($name ne $self->name){
    	if ($version) {
        	ThrowUserError('version_already_exists',
            	           {'name' => $version->name,
                	        'product' => $product->name});
    	}
    	
    	trick_taint($name);
    
    	$dbh->do("UPDATE bugs SET version = ?
              WHERE version = ? AND product_id = ?", undef,
              ($name, $self->name, $self->product_id));
              
        # if there are custom fields that use Version table as valid values list (system_table=1), update all their values 
        my @system_table_fields = grep { $_->system_table } Bugzilla->get_fields({ custom => 1, system_table => 1 });
		foreach my $field (@system_table_fields) {
			my $fieldname = $field->name;
		    if ($field->type == FIELD_TYPE_SINGLE_SELECT){
		    	$dbh->do("UPDATE bugs SET $fieldname = ?
              		WHERE $fieldname = ? AND product_id = ?", undef,
              			($name, $self->name, $self->product_id));
              			
		    } elsif ($field->type == FIELD_TYPE_MULTI_SELECT){
		    	my $tablename = "bug_$fieldname";
		    	my $bugs_list = $dbh->selectcol_arrayref("SELECT $tablename.bug_id FROM $tablename JOIN bugs ON $tablename.bug_id=bugs.bug_id
		    	  										WHERE $tablename.value = ? AND bugs.product_id = ?",undef,$self->name,$self->product_id);
				
		    	$dbh->do("UPDATE $tablename JOIN bugs ON $tablename.bug_id=bugs.bug_id
		    	 SET $tablename.value = ? WHERE $tablename.value = ? AND bugs.product_id = ?", undef,
              		($name, $self->name, $self->product_id));
              		
              	# update for the values in the bugs table as well
				foreach my $b (@$bugs_list){
					my $values_arr = $dbh->selectcol_arrayref("SELECT $tablename.value FROM $tablename JOIN bugs ON $tablename.bug_id=bugs.bug_id
		    	  											WHERE $tablename.bug_id=? AND bugs.product_id = ?",undef,$b,$self->product_id);
					my $values = join(" ",@$values_arr);
					$dbh->do("UPDATE bugs SET $fieldname=? WHERE bug_id=?",undef,$values,$b);
				}
              			
		    }
		}
    }
    
    trick_taint($name);
    trick_taint($status);
    trick_taint($sortkey);

    $dbh->do("UPDATE versions SET value = ?, status = ?, sortkey = ?
              WHERE product_id = ? AND value = ?", undef,
              ($name, $status, $sortkey, $self->product_id, $self->name));

    $self->{'value'} = $name;
    $self->{'status'} = $status;
    $self->{'sortkey'} = $sortkey;

    return 1;
}

###############################
#####     Accessors        ####
###############################

sub name       { return $_[0]->{'value'};      }
sub product_id { return $_[0]->{'product_id'}; }
sub status 	   { return $_[0]->{'status'}; }
sub sortkey	   { return $_[0]->{'sortkey'};	   }

###############################
#####     Subroutines       ###
###############################

sub create {
    my ($name, $product, $status, $sortkey) = @_;
    my $dbh = Bugzilla->dbh;

    # Cleanups and validity checks
    $name || ThrowUserError('version_blank_name');

    # Remove unprintable characters
    $name = clean_text($name);

    my $version = new Bugzilla::Version({ product => $product, name => $name });
    if ($version) {
        ThrowUserError('version_already_exists',
                       {'name' => $version->name,
                        'product' => $product->name});
    }

    # Add the new version
    trick_taint($name);
    trick_taint($status);
    trick_taint($sortkey);
    $dbh->do(q{INSERT INTO versions (value, product_id, status, sortkey)
               VALUES (?, ?, ?, ?)}, undef, ($name, $product->id, $status, $sortkey));

    return new Bugzilla::Version($dbh->bz_last_key('versions', 'id'));
}

1;

__END__

=head1 NAME

Bugzilla::Version - Bugzilla product version class.

=head1 SYNOPSIS

    use Bugzilla::Version;

    my $version = new Bugzilla::Version(1, 'version_value');

    my $product_id = $version->product_id;
    my $value = $version->value;
    my $status = $version->status;

    $version->remove_from_db;

    my $updated = $version->update($version_name, $product);

    my $version = $hash_ref->{'version_value'};

    my $version = Bugzilla::Version::create($version_name, $product, $status);

=head1 DESCRIPTION

Version.pm represents a Product Version object.

=head1 METHODS

=over

=item C<new($product_id, $value)>

 Description: The constructor is used to load an existing version
              by passing a product id and a version value.

 Params:      $product_id - Integer with a product id.
              $value - String with a version value.

 Returns:     A Bugzilla::Version object.

=item C<bug_count()>

 Description: Returns the total of bugs that belong to the version.

 Params:      none.

 Returns:     Integer with the number of bugs.

=item C<remove_from_db()>

 Description: Removes the version from the database.

 Params:      none.

 Returns:     none.

=item C<update($name, $product, $status)>

 Description: Update the value of the version.

 Params:      $name - String with the new version value.
              $product - Bugzilla::Product object the version belongs to.
              $status - status of the version (0 - Unreleased, 1 - Released, 2 - Archived)

 Returns:     An integer - 1 if the version has been updated, else 0.

=back

=head1 SUBROUTINES

=over

=item C<create($version_name, $product, $status)>

 Description: Create a new version for the given product.

 Params:      $version_name - String with a version value.
              $product - A Bugzilla::Product object.
              $status - status of the version (0 - Unreleased, 1 - Released, 2 - Archived)

 Returns:     A Bugzilla::Version object.

=back

=cut
