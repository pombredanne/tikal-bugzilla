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
# Contributor(s): Liya Jan <liya@tikalk.com>
#

use strict;

package Bugzilla::Browse;

use Bugzilla::Util;
use Bugzilla::Error;

###############################
####    Initialization     ####
###############################

use constant DB_COLUMNS => qw(
	browsedef.name
	browsedef.type
	browsedef.bugs_field_name
	browsedef.table_name
	browsedef.field_name
	browsedef.key_field_name
	browsedef.search_field_name
	browsedef.window
);

our $columns = join(", ", DB_COLUMNS);

###############################
####       Methods         ####
###############################

sub new {
    my $invocant = shift;
    my $class = ref($invocant) || $invocant;
    my $self = {};
    bless($self, $class);
    return $self->_init(@_);
}

sub _init {
    my $self = shift;
    my ($param) = @_;
    my $dbh = Bugzilla->dbh;

    my $browsedef;

	if ((defined $param->{'name'}) && (defined $param->{'type'})) {
    	$browsedef = $dbh->selectrow_hashref(qq{
            SELECT $columns FROM browsedef
            WHERE name = ? AND type=? }, undef, $param->{'name'}, $param->{'type'});
	} else {
        ThrowCodeError('bad_arg',
            {argument => 'param',
             function => 'Bugzilla::Browse::_init'});
    }

	return undef unless (defined $browsedef);

    foreach my $field (keys %$browsedef) {
        $self->{$field} = $browsedef->{$field};
    }
    return $self;
}


###############################
####      Accessors        ####
###############################

###############################
####      Subroutines      ####
###############################

sub GetBrowseDef {

	my ($type)=@_;

	my $dbh = Bugzilla->dbh;

	# get browse definitions
	my @browse_list;
	my $sth = $dbh->prepare(
             "SELECT name, bugs_field_name, table_name, field_name, key_field_name, search_field_name, window ".
             "FROM browsedef WHERE type=? ORDER BY window" );
    $sth->execute($type);

	while (my ($name, $bugs_field_name, $table_name, $field_name, $key_field_name, $search_field_name, $window) = $sth->fetchrow_array()) {
		push (@browse_list, {'browse_by' => $name,
						  'bugs_field_name' => $bugs_field_name,
						  'table_name' => $table_name,
						  'field_name' => $field_name,
						  'key_field_name' => $key_field_name,
						  'search_field_name' => $search_field_name,
						  'window' => $window });
	}

	return @browse_list;
}

sub GetFieldQueryResultsForProduct {
	my ($product_id,$bugs_field_name, $table_name, $field_name, $key_field_name) = @_;

	my $dbh = Bugzilla->dbh;

	my $query_opened;
	my $query_resolved;
	my $query_closed;
	if ($table_name eq "bugs") {
		$query_opened = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id=".$product_id." AND bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$bugs_field_name);
		$query_resolved = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id=".$product_id." AND bug_status in ('RESOLVED','VERIFIED') group by ".$bugs_field_name);
		$query_closed = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id=".$product_id." AND bug_status = 'CLOSED' group by ".$bugs_field_name);
	} elsif ($bugs_field_name eq "none") {
		$query_opened = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND bugs.bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$table_name.".".$field_name);
		$query_resolved = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND bugs.bug_status in ('RESOLVED','VERIFIED') group by ".$table_name.".".$field_name);
		$query_closed = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND bugs.bug_status = 'CLOSED' group by ".$table_name.".".$field_name);
	} else {
		$query_opened = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND .bugs.bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$table_name.".".$field_name);
		$query_resolved = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND bugs.bug_status in ('RESOLVED','VERIFIED') group by ".$table_name.".".$field_name);
		$query_closed = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id=".$product_id." AND bugs.bug_status = 'CLOSED' group by ".$table_name.".".$field_name);
	}

	return GetFieldQueryResults($query_opened,$query_resolved,$query_closed);
}

sub GetFieldQueryResultsForClassification {
	my ($classification_id,$products_list,$bugs_field_name, $table_name, $field_name, $key_field_name) = @_;

	my $dbh = Bugzilla->dbh;

	my $query_opened;
	my $query_resolved;
	my $query_closed;
	if ($table_name eq "bugs") {
		$query_opened = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id in (".$products_list.") AND bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$bugs_field_name);
		$query_resolved = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id in (".$products_list.") AND bug_status in ('RESOLVED','VERIFIED') group by ".$bugs_field_name);
		$query_closed = $dbh->prepare("SELECT ".$bugs_field_name.", count(*) from bugs where product_id in (".$products_list.") AND bug_status = 'CLOSED' group by ".$bugs_field_name);
	} elsif ($bugs_field_name eq "none") {
		$query_opened = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND bugs.bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$table_name.".".$field_name);
		$query_resolved = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND bugs.bug_status in ('RESOLVED','VERIFIED') group by ".$table_name.".".$field_name);
		$query_closed = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.bug_id =".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND bugs.bug_status = 'CLOSED' group by ".$table_name.".".$field_name);
	} else {
		$query_opened = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND .bugs.bug_status in ('NEW','ASSIGNED','REOPENED') group by ".$table_name.".".$field_name);
		$query_resolved = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND bugs.bug_status in ('RESOLVED','VERIFIED') group by ".$table_name.".".$field_name);
		$query_closed = $dbh->prepare("SELECT ".$table_name.".".$field_name.", count(*) from bugs,".$table_name." where bugs.".$bugs_field_name."=".$table_name.".". $key_field_name." AND bugs.product_id in (".$products_list.") AND bugs.bug_status = 'CLOSED' group by ".$table_name.".".$field_name);
	}

	return GetFieldQueryResults($query_opened,$query_resolved,$query_closed);
}

sub GetFieldQueryResults {

	my ($query_opened,$query_resolved,$query_closed)= @_;

	my %query_results;

	$query_opened->execute();
	while (my ($field_value, $count) = $query_opened->fetchrow_array()) {
		$query_results {$field_value} {'opened' }= $count;
	}
	$query_resolved->execute();
	while (my ($field_value, $count) = $query_resolved->fetchrow_array()) {
		$query_results {$field_value} {'resolved'} = $count;
	}
	$query_closed->execute();
	while (my ($field_value, $count) = $query_closed->fetchrow_array()) {
		$query_results {$field_value} {'closed'} = $count;
	}
	return \%query_results;

}

sub GetTotalForProduct {
	my ($product_id, $statuses) = @_;

	my $dbh = Bugzilla->dbh;
	my $total = $dbh->selectcol_arrayref("
            SELECT count(*) FROM bugs WHERE product_id = $product_id AND bug_status IN ( $statuses)");
    return $total->[0];
}

sub GetTotalForClassification {
	my ($products_list, $statuses) = @_;

	my $dbh = Bugzilla->dbh;
	my $total = $dbh->selectcol_arrayref("
            SELECT count(*) FROM bugs WHERE product_id in ($products_list) AND bug_status IN ($statuses)");
    return $total->[0];
}

1;
