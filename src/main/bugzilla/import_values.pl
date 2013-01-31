#!/usr/bin/perl -w
# -*- Mode: perl; indent-tabs-mode: nil -*-
#
# Import values for custom fields
# Arguments: custom field name - mandatory
#            path to values file - mandatory
#            create sortkey indicator - optional - by default, all values are created with sortkey 0, if you want to create the sortkeys, run it with the 3d argument (any value)
#
# Run this script in bugzilla home folder:
# ./import_values.pl <field name> <path to the file with values> [<create sortkey?>]
# like
#./import_values.pl cf_customers /home/opencm/customers-values.txt
# or
# /import_values.pl cf_customers /home/opencm/customers-values.txt yes
# 
# Important - if the values file is created on Windows, run dos2unix on it before running the script.
# 

use strict;
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;

my $dbh = Bugzilla->dbh;

my $field_name = $ARGV[0];
my $file = $ARGV[1];
my $create_sortkey = $ARGV[2];

if (!$field_name || $field_name eq "" || !$file || $file eq "") {
	print "Field name and values file path cannot be empty!\n";
	exit 1;
}

my $field = new Bugzilla::Field({'name' => $field_name, 'custom' => 1});
if (!$field){
	print "Custom field $field_name does not exist!\n";	
	exit 1;
} 
if (!($field->is_select && !$field->system_table)){
	print "Field $field_name can not have predefined values!\n";
	exit 1;
}

open( CP, $file ) || die "\nCan not open " . $file . "\n";
my @values;
while ( my $value = <CP> ) {
	$value =~ s/\n$//;
	my $sortkey = 0;
	if ($create_sortkey){
		$sortkey = $dbh->selectrow_array("SELECT max(sortkey) FROM $field_name",undef);
		$sortkey++;
	}
	my $value_test = $dbh->selectrow_array("SELECT value FROM $field_name WHERE value=?",undef,$value);
	if ($value_test){
		print "Value '$value' already exists for field '$field_name' - IGNORED!\n";
	} elsif (length($value) > MAX_FIELD_VALUE_SIZE) {
		print "The value of a field is limited to ".MAX_FIELD_VALUE_SIZE." characters. Value '$value' is too long (".length($value)." characters). - IGNORED!\n";
	} else {
		my $created_value = Bugzilla::Field::Choice->type($field)->create({
	        value   => $value, 
	        sortkey => $sortkey,
	        is_open => 1,
	        visibility_value_id => "",
	    });	
	}
}
