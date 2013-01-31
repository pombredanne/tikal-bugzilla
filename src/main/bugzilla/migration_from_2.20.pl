#!/usr/bin/perl -w
# -*- Mode: perl; indent-tabs-mode: nil -*-
#

use strict;
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;
my $dbh = Bugzilla->dbh;

# get old params
my $s = new Safe;

$s->rdo("data/params_old");
die "Error reading data/params_old: $!" if $!;
die "Error evaluating data/params_old: $@" if $@;

# Now read the old params back out from the sandbox
my %params = %{$s->varglob('param')};

# migrate some Tikal fields to the custom fields
# 1 - true, 0 - false
my $fixed_in_2_cf = 0;
my $target_version_2_cf = 0; 
my $target_version_2_milestone = 0;
my $found_in_build_2_cf = 0;
my $fixed_in_build_2_cf = 0;
my $reopen_resolution_2_cf = 0;
my $qaimpact_2_cf = 0;
my $test_guildelines_2_cf = 0;
my $doc_req_2_cf = 0;
my $doc_guildelines_2_cf = 0;
my $customers_2_cf = 0;
my $module_2_cf = 0;

# migrate old Tikal custom fields
if ($params{'usecustomfields'}){
	# product field id and values for visibility 
	my $product_field_id = $dbh->selectrow_array("SELECT id FROM fielddefs WHERE name='product'",undef);
	
	# migrate existing custom fileds to the new implementation
	my %custom_fields;
	my $cf_list = $dbh->selectall_arrayref("SELECT id, name, type, valid_exp, mandatory, default_value, showonnew FROM customfields", undef);
	foreach my $field (@$cf_list) {
        my ($id, $name, $old_type, $valid_exp, $mandatory, $default_value, $showonnew) = @$field;
        my $desc = $dbh->selectrow_array("SELECT description FROM fielddefs WHERE name=?",undef,$name);
        my $cf_products = $dbh->selectcol_arrayref("SELECT product_id FROM products_customfields WHERE cf_id=?",undef,$id);
        my $cf_entities = $dbh->selectcol_arrayref("SELECT entity_id FROM entity_customfields WHERE cf_id=?",undef,$id);
		        
        # validations and fixes
        my $old_name = $name;
        if ($name !~ /^cf_/){
        	$name = "cf_".$name;
        }
		        
        my $type;
        if ($old_type eq "any"){
        	$type = FIELD_TYPE_FREETEXT;
        } elsif ($old_type eq "single") {
        	$type = FIELD_TYPE_SINGLE_SELECT;
        } elsif ($old_type eq "multi" || $old_type eq "multidouble") {
        	$type = FIELD_TYPE_MULTI_SELECT;
        } elsif ($old_type eq "textarea") {
        	$type = FIELD_TYPE_TEXTAREA;
        } else {
        	print "Unknown custom fields type - $old_type\n";
        	exit 1;
        }
		        
        for my $e (@$cf_entities){
        	if ($e ne "0"){
        		print "Custom field $name is defined not for 'All' entities - NOT SUPPORTED at the moment - use create/edit templates to support it!\n";
        	}
        }
		        
        my $cf_p_id = 0;
        if (scalar @$cf_products > 1){
        	print "Custom field $name is defined for multiple products - NOT SUPPORTED - - use create/edit templates to support it!\n";
        } else {
			$cf_p_id = $cf_products->[0];         	
        }
		        
		my $field = new Bugzilla::Field({'name' => $old_name});
		if ($field){
	    	$field->set_description($desc);
		    $field->set_sortkey(0);
		    $field->set_in_new_bugmail($showonnew);
		    $field->set_enter_bug($showonnew);
		    $field->set_obsolete(0);
		    $field->set_system(0);
		    $field->set_system_table(0);
		    $field->set_mandatory($mandatory ? FIELD_MANDATORY_ALWAYS : FIELD_NOT_MANDATORY);
		    $field->set_default_value($default_value);
		    $field->set_visibility_field($cf_p_id > 0 ? $product_field_id : "");
		    $field->set_visibility_value($cf_p_id > 0 ? $cf_p_id : "");
		    $field->update();
		    # update the name and type to the new one
		    $dbh->do("UPDATE fielddefs SET name = ?, type = ?, custom = 1, buglist = 1 WHERE name = ?",undef,$name,$type,$old_name);
				    
			$field->{'name'} = $name;
			$field->{'type'} = $type;
            # Create the database column that stores the data for this field.
         	my $sql_def;
            if ($type == FIELD_TYPE_FREETEXT || $type == FIELD_TYPE_MULTI_SELECT ) {
            	$sql_def = { TYPE => 'varchar(255)'};
            } elsif($type == FIELD_TYPE_TEXTAREA) {
            	$sql_def = { TYPE => 'MEDIUMTEXT'};
            } elsif($type == FIELD_TYPE_SINGLE_SELECT) {
            	$sql_def = { TYPE => 'varchar(64)', NOTNULL => 1, DEFAULT => "'---'" },
            }
            $dbh->bz_add_column('bugs', $name, $sql_def);

	        if ($type == FIELD_TYPE_SINGLE_SELECT || $type == FIELD_TYPE_MULTI_SELECT) {
	            # Create the table that holds the legal values for this field.
	            $dbh->bz_add_field_tables($field);
	        }
			
	        if ($type == FIELD_TYPE_SINGLE_SELECT) {
	            # Insert a default value of "---" into the legal values table.
	            $dbh->do("INSERT INTO $name (value) VALUES ('---')");
	        }
		    print "Custom field $old_name is updated to $name and to the new implementation.\n";
				    
	    } else {
	    	$field = Bugzilla::Field->create({
				        name        => $name,
				        description => $desc,
				        type        => $type,
				        sortkey     => "",
				        mailhead    => $showonnew,
				        enter_bug   => $showonnew,
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> $mandatory ? FIELD_MANDATORY_ALWAYS : FIELD_NOT_MANDATORY,
				        default_value	=> $default_value,
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => $cf_p_id > 0 ? $product_field_id : "",
				        visibility_value_id => $cf_p_id > 0 ? $cf_p_id : "",
				        value_field_id => "",
				    });
			print "Custom field $name is created.\n";
	    }
			    
	    # set valid values for the select field
	    if ($field->is_select) {
		    my @vvalues = split('\|', $valid_exp);
		    foreach my $vv (@vvalues){
				if ($vv ne ""){
					$vv =~ s/^\s+//;
					$vv =~ s/\s+$//;
					$dbh->do("INSERT INTO $name (value) VALUES (?)",undef,$vv);
				}
		    }
	    }
			    
	    # move bug values of the field to correct table
	    my $cf_values = $dbh->selectall_arrayref("SELECT bug_id, value FROM bugs_customfields WHERE cf_id=?",undef,$id );
	    if ($cf_values){
	    	if ($type == FIELD_TYPE_MULTI_SELECT){
		    	foreach my $v (@$cf_values){
		    		my ($bug_id, $value) = @$v;
		    		my @bv = sort(split('\|', $value));
		    		foreach my $v (@bv){
			    		$v =~ s/^\s+//; 
			    		$v =~ s/\s+$//; 
			    		$dbh->do("INSERT INTO bug_$name (bug_id, value) VALUES (?,?)",undef,$bug_id,$v);
		    		}
		    		$value = join(' ', @bv); # get the sorted list 
		    		$dbh->do("UPDATE bugs set $name=? WHERE bug_id=?",undef,$value,$bug_id);
		    	}
		    } else {
		    	foreach my $v (@$cf_values){
		    		my ($bug_id, $value) = @$v;
		    		$value =~ s/^\s+//;  
		    		$value =~ s/\s+$//;
		    		$dbh->do("UPDATE bugs set $name=? WHERE bug_id=?",undef,$value,$bug_id);
		    	}
		    }
	    }
		# update Saved Searches & Reports with new field names			
		$dbh->do("UPDATE namedqueries SET query=REPLACE(query,?,?) WHERE (INSTR(query,? )>0)",
					undef,
					$old_name,
					$name,
					$old_name);
		$dbh->do("UPDATE namedreports SET report=REPLACE(report,?,?) WHERE (INSTR(report,? )>0)",
					undef,
					$old_name,
					$name,
					$old_name);
		    
	} # foreach custom field

	print "Custom fields migrated - Set sortkeys manually!\n";
	print "Check the warnings for Entity/Products in custom fields!\n";
	print "Removing old tables: customfields, products_customfields, entity_customfields, bugs_customfields...\n";
	$dbh->bz_drop_table("customfields");
	$dbh->bz_drop_table("products_customfields");
	$dbh->bz_drop_table("entity_customfields");
	$dbh->bz_drop_table("bugs_customfields");
}
	
# fix DB - remove 'dead' records
$dbh->do("delete from target_version where value not in (select value from milestones)");
$dbh->do("delete from fixed_in where value not in (select value from milestones)");
$dbh->do("delete from target_version where bug_id not in (select bug_id from bugs)");
$dbh->do("delete from fixed_in where bug_id not in (select bug_id from bugs)");

if ($params{'use_fixed_in'} || $params{'use_target_version'}){
	# add missing milestone to the versions list as UNRELEASED
	my $milestones_list = $dbh->selectall_arrayref("SELECT value,product_id,invisible FROM milestones",undef);
	foreach my $ml (@$milestones_list){
		my ($value,$product_id,$invisible) = @$ml;
		my $chkv = $dbh->selectrow_array("SELECT value FROM versions WHERE value=? and product_id=?",undef,$value,$product_id);
		if (!$chkv){
			my $status = $invisible ? VERSION_STATUS_ARCHIVED : VERSION_STATUS_UNRELEASED;
			$dbh->do("INSERT INTO versions (value,product_id,status) VALUES (?,?,?)",undef,$value,$product_id,$status);
		}
	}
	# fix versions status that do not appear in milestones list and not ARCHIVED already to FINAL 
	my $versions_list = $dbh->selectall_arrayref("SELECT value,product_id FROM versions WHERE status!=?",undef,VERSION_STATUS_ARCHIVED);
	foreach my $vv (@$versions_list){
		my ($value,$product_id) = @$vv;
		my ($chkm, $minvs) = $dbh->selectrow_array("SELECT value,invisible FROM milestones WHERE value=? and product_id=?",undef,$value,$product_id);
		if (!$chkm || ($chkm && $minvs == 1)){
			$dbh->do("UPDATE versions SET status=? WHERE value=? and product_id=?",undef,VERSION_STATUS_FINAL,$value,$product_id);
		}
	}
	
}


# Fixed In - to multi-valued field, system, system_table - Version
if ($params{'use_fixed_in'}){
	$fixed_in_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_fixed_in",
				        description => "Fixed In",
				        type        => FIELD_TYPE_MULTI_SELECT,
				        sortkey     => "500",
				        mailhead    => 0,
				        enter_bug   => 0,
				        obsolete    => 0,
				        system    	=> 1,
				        system_table => 1,
				        mandatory	=> $params{'mandatory_fixed_in'} ? FIELD_MANDATORY_FOR_RESOLVED_FIXED : FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_fixed_in is created.\n";
	
	my $bug_values = $dbh->selectall_arrayref("SELECT value, bug_id FROM fixed_in",undef);
	my %full_value;
	foreach my $bv (@$bug_values){
		my ($value,$bug_id) = @$bv;
		my $chkvalue = $dbh->selectrow_array("SELECT value FROM bug_cf_fixed_in WHERE value=? AND bug_id=?",undef,$value,$bug_id);
		if(!$chkvalue){
			$dbh->do("INSERT INTO bug_cf_fixed_in (value,bug_id) VALUES (?,?)",undef,$value,$bug_id);
			if ($full_value{$bug_id}){
				$full_value{$bug_id} .= $value." "; 
			} else {
				$full_value{$bug_id} = $value." "; 
			}
		}
	}
	foreach my $bid (keys %full_value){
		# sort the list and save in bugs
		my @sorted_values = sort(split(" ",$full_value{$bid}));
		$dbh->do("UPDATE bugs SET cf_fixed_in=? WHERE bug_id=?",undef,join(' ', @sorted_values),$bid);
	}
	
}

#### Fixed In - to dropdown field
#### TBD this as an option
# $fixed_in_2_cf = 1;

if ($fixed_in_2_cf) {
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('fixed_in','cf_fixed_in');
	update_bug_activity('bugs_fixed_in','cf_fixed_in');
} else {
	# remove rows in bugs_activity and fielddefs
	update_bug_activity('fixed_in');
	update_bug_activity('bugs_fixed_in');
}

# remove old tables and fields
$dbh->bz_drop_column('bugs','bugs_fixed_in');		
$dbh->bz_drop_table('fixed_in');


###############################################################
# Target Version - to multi-valued field, system, system_table - Version
if ($params{'use_target_version'}){
	$target_version_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_target_version",
				        description => "Target Version",
				        type        => FIELD_TYPE_MULTI_SELECT,
				        sortkey     => "400",
				        mailhead    => 1,
				        enter_bug   => 1,
				        obsolete    => 0,
				        system    	=> 1,
				        system_table => 1,
				        mandatory	=> $params{'mandatory_target_version'} ? FIELD_MANDATORY_ALWAYS : FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_target_version is created.\n";

	my $bug_values = $dbh->selectall_arrayref("SELECT value, bug_id FROM target_version",undef);
	my %full_value;
	foreach my $bv (@$bug_values){
		my ($value,$bug_id) = @$bv;
		my $chkvalue = $dbh->selectrow_array("SELECT value FROM bug_cf_target_version WHERE value=? AND bug_id=?",undef,$value,$bug_id);
		if(!$chkvalue){
			$dbh->do("INSERT INTO bug_cf_target_version (value,bug_id) VALUES (?,?)",undef,$value,$bug_id);
			if ($full_value{$bug_id}){
				$full_value{$bug_id} .= $value." "; 
			} else {
				$full_value{$bug_id} = $value." "; 
			}
		}
	}
	foreach my $bid (keys %full_value){
		# sort the list and save in bugs
		my @sorted_values = sort(split(" ",$full_value{$bid}));
		$dbh->do("UPDATE bugs SET cf_target_version=? WHERE bug_id=?",undef,join(' ', @sorted_values),$bid);
	}
}

#### Target Version - to Target Milestone
#### TBD this as an option
#my $target_version_2_milestone = 1;

if ($target_version_2_cf) {
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('bugs_target_version','cf_target_version');
	update_bug_activity('target_version','cf_target_version');
	# Update target_version in browsedef
	$dbh->do("UPDATE browsedef SET table_name='bug_cf_target_version',search_field_name='cf_target_version' WHERE table_name='target_version'");
} elsif ($target_version_2_milestone) {
	update_bug_activity('bugs_target_version','target_milestone');
	update_bug_activity('target_version','target_milestone');
	# Update target_version in browsedef
	$dbh->do("UPDATE browsedef SET name='Target Milestone',bugs_field_name='target_milestone',table_name=NULL,key_field_name=NULL,search_field_name='target_milestone' WHERE table_name='target_version'");
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('bugs_target_version');
	update_bug_activity('target_version');
	# Update target_version in browsedef
	$dbh->do("UPDATE browsedef SET name='Target Milestone',bugs_field_name='target_milestone',table_name=NULL,key_field_name=NULL,search_field_name='target_milestone' WHERE table_name='target_version'");
}


# remove old tables and fields
$dbh->bz_drop_column('bugs','bugs_target_version');		
$dbh->bz_drop_table('target_version');

if (!$target_version_2_milestone){
	# clean up milestones table if not in use..
	$dbh->do("UPDATE products SET defaultmilestone='---';");
	$dbh->do("UPDATE bugs set target_milestone='---'");		
	$dbh->do("DELETE FROM milestones");
	my $products_ids = $dbh->selectcol_arrayref("SELECT id FROM products");
	foreach my $p (@$products_ids){
		$dbh->do("INSERT INTO milestones (value,product_id) VALUES ('---',?)",undef,$p);
	}
}

#############################################################################################
# Found in Build - to free text field
if ($params{'use_found_in_build'}){
	$found_in_build_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_found_in_build",
				        description => "Found In Build",
				        type        => FIELD_TYPE_FREETEXT,
				        sortkey     => "200",
				        mailhead    => 1,
				        enter_bug   => 1,
				        obsolete    => 0,
				        system    	=> 1,
				        system_table => 0,
				        mandatory	=> $params{'mandatory_found_in_build'} ? FIELD_MANDATORY_FOR_NEW : FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_found_in_build is created.\n";
	
	
}
if ($found_in_build_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('found_in_build','cf_found_in_build');
	# remove old tables and fields
	$dbh->bz_drop_column('bugs','cf_found_in_build');		
	$dbh->bz_rename_column('bugs', 'found_in_build', 'cf_found_in_build');	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('found_in_build');
	# remove old tables and fields
	$dbh->bz_drop_column('bugs','found_in_build');		
}
	
###########################################################################################################################################	
# Fixed in Build - to free text field
if ($params{'use_fixed_in_build'}){
	$fixed_in_build_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_fixed_in_build",
				        description => "Fixed In Build",
				        type        => FIELD_TYPE_FREETEXT,
				        sortkey     => "300",
				        mailhead    => 0,
				        enter_bug   => 0,
				        obsolete    => 0,
				        system    	=> 1,
				        system_table => 0,
				        mandatory	=> $params{'mandatory_fixed_in_build'} ? FIELD_MANDATORY_FOR_RESOLVED_FIXED : FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_fixed_in_build is created.\n";
	
}
if ($fixed_in_build_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('fixed_in_build','cf_fixed_in_build');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','cf_fixed_in_build');
	$dbh->bz_rename_column('bugs', 'fixed_in_build', 'cf_fixed_in_build');
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('fixed_in_build');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','fixed_in_build');
}

################################################################################################################################################	
# Reopen Resolution - to dropdown field
if ($params{'use_reopen_resolution'}){
	$reopen_resolution_2_cf = 1;
	my $status_field_id = $dbh->selectrow_array("SELECT id FROM fielddefs WHERE name='bug_status'",undef);
	my $reopened_status_value_id = $dbh->selectrow_array("SELECT id FROM bug_status WHERE value='REOPENED'",undef);
	my $field = Bugzilla::Field->create({
				        name        => "cf_reopen_resolution",
				        description => "Reopen Resolution",
				        type        => FIELD_TYPE_SINGLE_SELECT,
				        sortkey     => "1100",
				        mailhead    => 0,
				        enter_bug   => 0,
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_MANDATORY_FOR_REOPENED,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => $status_field_id,
				        visibility_value_id => $reopened_status_value_id,
				        value_field_id => "",
				    });
	print "Custom field cf_reopen_resolution is created.\n";
	my $values = $dbh->selectall_arrayref("SELECT value, sortkey FROM reopen_resolution",undef);
	foreach my $v (@$values){
		my ($value,$sortkey) = @$v;
		$dbh->do("INSERT INTO cf_reopen_resolution (value,sortkey) VALUES (?,?)",undef,$value,$sortkey);
	}
	
}

if ($reopen_resolution_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('reopen_resolution','cf_reopen_resolution');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','cf_reopen_resolution');
	$dbh->bz_alter_column('bugs', 'reopen_resolution', {TYPE => 'varchar(255)'});
	$dbh->bz_rename_column('bugs', 'reopen_resolution', 'cf_reopen_resolution');	
	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('reopen_resolution');
	$dbh->bz_drop_column('bugs','reopen_resolution');
}

$dbh->bz_drop_table('reopen_resolution');

################################################################################################################################################	
# QA Impact - to dropdown field
if ($params{'use_qaimpact'}){
	$qaimpact_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_qaimpact",
				        description => "QA Impact",
				        type        => FIELD_TYPE_SINGLE_SELECT,
				        sortkey     => "600",
				        mailhead    => 0,
				        enter_bug   => $params{'use_qaimpact_fornew'},
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_MANDATORY_FOR_RESOLVED_FIXED,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_qaimpact is created.\n";
	my $values = $dbh->selectall_arrayref("SELECT value, sortkey FROM qaimpact",undef);
	foreach my $v (@$values){
		my ($value,$sortkey) = @$v;
		$dbh->do("INSERT INTO cf_qaimpact (value,sortkey) VALUES (?,?)",undef,$value,$sortkey);
	}

# Test Guidelines - to Large Textbox field
	$test_guildelines_2_cf = 1;
	$field = Bugzilla::Field->create({
				        name        => "cf_test_guidelines",
				        description => "Test Guidelines",
				        type        => FIELD_TYPE_TEXTAREA,
				        sortkey     => "700",
				        mailhead    => 0,
				        enter_bug   => $params{'use_qaimpact_fornew'},
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_MANDATORY_FOR_RESOLVED_FIXED,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_test_guidelines is created.\n";
	
}

if ($qaimpact_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('qaimpact','cf_qaimpact');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','cf_qaimpact');
	$dbh->bz_alter_column('bugs', 'qaimpact', {TYPE => 'varchar(255)'});
	$dbh->bz_rename_column('bugs', 'qaimpact', 'cf_qaimpact');	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('qaimpact');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','qaimpact');
}
$dbh->bz_drop_table('qaimpact');

if ($test_guildelines_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('test_guidelines','cf_test_guidelines');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','cf_test_guidelines');
	$dbh->bz_alter_column('bugs', 'test_guidelines', {TYPE => 'MEDIUMTEXT'});
	$dbh->bz_rename_column('bugs', 'test_guidelines', 'cf_test_guidelines');	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('test_guidelines');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','test_guidelines');
}

####################################################################################################
# Doc Required - to dropdown field
if ($params{'use_doc_required'}){
	$doc_req_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_doc_required",
				        description => "Doc Required",
				        type        => FIELD_TYPE_SINGLE_SELECT,
				        sortkey     => "800",
				        mailhead    => 0,
				        enter_bug   => 0,
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_MANDATORY_FOR_RESOLVED_FIXED,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_doc_required is created.\n";
	my $values = $dbh->selectall_arrayref("SELECT value, sortkey FROM doc_required",undef);
	foreach my $v (@$values){
		my ($value,$sortkey) = @$v;
		$dbh->do("INSERT INTO cf_doc_required (value,sortkey) VALUES (?,?)",undef,$value,$sortkey);
	}

# Doc Description - to Large Textbox field
	$doc_guildelines_2_cf = 1;
	$field = Bugzilla::Field->create({
				        name        => "cf_doc_guidelines",
				        description => "Doc Guidelines",
				        type        => FIELD_TYPE_TEXTAREA,
				        sortkey     => "900",
				        mailhead    => 0,
				        enter_bug   => 0,
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_MANDATORY_FOR_RESOLVED_FIXED,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_doc_guidelines is created.\n";
}

if ($doc_req_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('doc_required','cf_doc_required');
	# remove old tables and fields
	$dbh->bz_drop_column('bugs','cf_doc_required');
	$dbh->bz_rename_column('bugs', 'doc_required', 'cf_doc_required');	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('doc_required');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','doc_required');
}
$dbh->bz_drop_table('doc_required');

if ($doc_guildelines_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('doc_guidelines','cf_doc_guidelines');
	# remove old tables and fields
	$dbh->bz_drop_column('bugs','cf_doc_guidelines');
	$dbh->bz_alter_column('bugs', 'doc_guidelines', {TYPE => 'MEDIUMTEXT'});
	$dbh->bz_rename_column('bugs', 'doc_guidelines', 'cf_doc_guidelines');	
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('doc_guidelines');
	# remove old tables and fields	
	$dbh->bz_drop_column('bugs','doc_guidelines');
}

###########################################################################################################	
# Customers - to dropdown field
if ($params{'use_customers'}){
	$customers_2_cf = 1;
	my $field = Bugzilla::Field->create({
				        name        => "cf_customers",
				        description => "Customers",
				        type        => FIELD_TYPE_MULTI_SELECT,
				        sortkey     => "1000",
				        mailhead    => 1,
				        enter_bug   => 1,
				        obsolete    => 0,
				        system    	=> 0,
				        system_table => 0,
				        mandatory	=> FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => "",
				    });
	print "Custom field cf_customers is created.\n";
	my $values = $dbh->selectall_arrayref("SELECT id, name FROM customerdefs",undef);
	my %customers;
	foreach my $v (@$values){
		my ($id,$value) = @$v;
		$dbh->do("INSERT INTO cf_customers (value) VALUES (?)",undef,$value);
		$customers{$id} = $value;
	}
	my $bug_values = $dbh->selectall_arrayref("SELECT customerid, bug_id FROM customers",undef);
	my %full_value;
	foreach my $bv (@$bug_values){
		my ($cid,$bug_id) = @$bv;
		$dbh->do("INSERT INTO bug_cf_customers (value,bug_id) VALUES (?,?)",undef,$customers{$cid},$bug_id);
		if ($full_value{$bug_id}){
			$full_value{$bug_id} .= $customers{$cid}." "; 
		} else {
			$full_value{$bug_id} = $customers{$cid}." "; 
		}
	}
	foreach my $bid (keys %full_value){
		# sort the list and save in bugs
		my @sorted_values = sort(split(" ",$full_value{$bid}));
		$dbh->do("UPDATE bugs SET cf_customers=? WHERE bug_id=?",undef,join(' ', @sorted_values),$bid);
	}
	
}

if ($customers_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('customers','cf_customers');
	update_bug_activity('customersctg','cf_customers');
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('customers');
	update_bug_activity('customersctg');
}
# remove old tables and fields
$dbh->bz_drop_column('bugs','customers');
$dbh->bz_drop_table('customerdefs');
$dbh->bz_drop_table('customers');
$dbh->bz_drop_table('customersctg');

###########################################################################################################################
# Module - to dropdown field by Product
if ($params{'use_module'}){
	$module_2_cf = 1;
	my $product_field_id = $dbh->selectrow_array("SELECT id FROM fielddefs WHERE name='product'",undef);
	my $field = Bugzilla::Field->create({
				        name        => "cf_module",
				        description => $params{'module_field_name'},
				        type        => FIELD_TYPE_SINGLE_SELECT,
				        sortkey     => "100",
				        mailhead    => 1,
				        enter_bug   => 1,
				        obsolete    => 0,
				        system    	=> 1,
				        system_table => 0,
				        mandatory	=> $params{'mandatory_module'} ? FIELD_MANDATORY_ALWAYS : FIELD_NOT_MANDATORY,
				        default_value	=> "",
				        custom      => 1,
				        buglist     => 1,
				        visibility_field_id => "",
				        visibility_value_id => "",
				        value_field_id => $product_field_id,
				    });
	print "Custom field cf_module is created.\n";
	my $values = $dbh->selectall_arrayref("SELECT id, name, product_id FROM modules",undef);
	my %modules;
	foreach my $v (@$values){
		my ($id,$name,$product_id) = @$v;
		$modules{$id} = $name;
		# check if this value already exists for another product
		my $mm = $dbh->selectrow_array ("SELECT value FROM cf_module WHERE value=?",undef,$name);
		if ($mm){
			# update visibility to ALL
			print "Module value $name already exists, changing visibility...\n";
			$dbh->do("UPDATE cf_module SET visibility_value_id=NULL WHERE value=?",undef,$name);
		} else {
			# add the value
			$dbh->do("INSERT INTO cf_module (value,visibility_value_id) VALUES (?,?)",undef,$name,$product_id);
		}
		
	}
	my $bug_values = $dbh->selectall_arrayref("SELECT module_id, bug_id FROM bugs",undef);
	foreach my $bv (@$bug_values){
		my ($mid,$bug_id) = @$bv;
		$dbh->do("UPDATE bugs SET cf_module=? WHERE bug_id=?",undef,$modules{$mid},$bug_id);
	}
	
}

if ($module_2_cf){
	# update bugs_activity with the new field id and remove the old ones
	update_bug_activity('module','cf_module');
} else {
	# remove rows in bugs_activity and fielddefs 
	update_bug_activity('module');
}
# remove old tables and fields
$dbh->bz_drop_column('bugs','module_id');
$dbh->bz_drop_table('modules');
	
###########################################################################################################
# DefaultCC - to new implementation
if ($params{'use_initialcclist'}){
	my $initcc = $dbh->selectall_arrayref("SELECT id, initialcclist FROM components",undef);
	foreach my $cc (@$initcc){
		my ($id,$initialcclist) = @$cc;
		my @cc_list = split (',',$initialcclist);
		foreach my $u (@cc_list){
			$dbh->do("INSERT INTO component_cc (user_id,component_id) VALUES (?,?)",undef,$u,$id);
		}
	}
}
# remove old tables and fields
$dbh->bz_drop_column('components','initialcclist');

# fix crm bug activity
# update bugs_activity with the new field id and remove the old ones
update_bug_activity('crm_id','crm');
	
##########################################################################################################################
# Saved Searches & Reports - new field names 
# changed fields
my @changed_fields = (
				{'old' => 'target_version', 'new' => 'cf_target_version'},
				{'old' => 'bugs_target_version', 'new' => 'cf_target_version'},
				{'old' => 'bugs_cf_target_version', 'new' => 'cf_target_version'},
				{'old' => 'fixed_in', 'new' => 'cf_fixed_in'},
				{'old' => 'bugs_fixed_in', 'new' => 'cf_fixed_in'},
				{'old' => 'bugs_cf_fixed_in', 'new' => 'cf_fixed_in'},	 
				{'old' => 'found_in_build', 'new' => 'cf_found_build'},
				{'old' => 'fixed_in_build', 'new' => 'cf_fixed_in_build'},
				{'old' => 'reopen_resolution', 'new' => 'cf_reopen_resolution'},
				{'old' => 'module', 'new' => 'cf_module'},
				{'old' => 'module_id', 'new' => 'cf_module'},
				{'old' => 'qaimpact', 'new' => 'cf_qaimpact' },
				{'old' => 'test_guidelines', 'new' => 'cf_test_guidelines' },
				{'old' => 'doc_required', 'new' => 'cf_doc_required' },
				{'old' => 'doc_guidelines', 'new' => 'cf_doc_guidelines' },
				{'old' => 'customers', 'new' => 'cf_customers'},
				{'old' => 'crm_id', 'new' => 'crm'},
				{'old' => 'crm_list', 'new' => 'crm'});
				
foreach my $changed (@changed_fields){
	$dbh->do("UPDATE namedqueries SET query=REPLACE(query,?,?) WHERE (INSTR(query,? )>0)",
				undef,
				$changed->{'old'},
				$changed->{'new'},
				$changed->{'old'});
	$dbh->do("UPDATE namedreports SET report=REPLACE(report,?,?) WHERE (INSTR(report,? )>0)",
				undef,
				$changed->{'old'},
				$changed->{'new'},
				$changed->{'old'});
}
	
		
		
# Saved public searches - to new implementation
my $public_searches = $dbh->selectall_arrayref("SELECT id, group_id,userid FROM namedqueries WHERE group_id != 0",undef);
foreach my $ps (@$public_searches){
	my ($id,$group_id,$userid) = @$ps;
	$dbh->do("INSERT INTO namedquery_group_map (namedquery_id,group_id) VALUES (?,?)",undef,$id,$group_id);
	my $group = new Bugzilla::Group($group_id);
    my $members = $group->members_non_inherited;
    foreach my $member (@$members) {
    	next if $member->id == $userid;
    	my $user_link_in_footer = $dbh->selectrow_array("SELECT 1 FROM namedqueries_link_in_footer
          									WHERE namedquery_id = ? AND user_id = ?", 
        									undef, $id, $member->id) || 0;
        if (!$user_link_in_footer) {
        	$dbh->do("INSERT INTO namedqueries_link_in_footer (namedquery_id, user_id) VALUES (?, ?)",undef,$id,$member->id);
        }
    }
}
$dbh->bz_drop_column('namedqueries','group_id');

# Saved public reports - to new implementation
my $public_reports = $dbh->selectall_arrayref("SELECT id, group_id,userid FROM namedreports WHERE group_id != 0",undef);
foreach my $ps (@$public_reports){
	my ($id,$group_id,$userid) = @$ps;
	$dbh->do("INSERT INTO namedreport_group_map (namedreport_id,group_id) VALUES (?,?)",undef,$id,$group_id);
	my $group = new Bugzilla::Group($group_id);
    my $members = $group->members_non_inherited;
    foreach my $member (@$members) {
    	next if $member->id == $userid;
    	my $user_link_in_footer = $dbh->selectrow_array("SELECT 1 FROM namedreports_link_in_footer
          									WHERE namedreport_id = ? AND user_id = ?", 
        									undef, $id, $member->id) || 0;
   		if (!$user_link_in_footer) {
   			$dbh->do("INSERT INTO namedreports_link_in_footer (namedreport_id, user_id) VALUES (?, ?)",undef,$id,$member->id)
   		}
    }
}
$dbh->bz_drop_column('namedreports','group_id');

# fix bad dates
my $bugs_list = $dbh->selectall_arrayref("SELECT bug_id,creation_ts,lastdiffed FROM bugs WHERE delta_ts='0000-00-00'",undef);
foreach my $bug (@$bugs_list){
	my ($bug_id,$creation_ts,$lastdiffed) = @$bug;
	if ($lastdiffed){
		$dbh->do("UPDATE bugs set delta_ts=? WHERE bug_id=?",undef,$lastdiffed,$bug_id);
	} else {
		$dbh->do("UPDATE bugs set delta_ts=? WHERE bug_id=?",undef,$creation_ts,$bug_id);
	}
}
$bugs_list = $dbh->selectall_arrayref("SELECT bug_id,delta_ts FROM bugs WHERE creation_ts='0000-00-00'",undef);
foreach my $bug (@$bugs_list){
	my ($bug_id,$delta_ts) = @$bug;
	if ($delta_ts){
		$dbh->do("UPDATE bugs set creation_ts =? WHERE bug_id=?",undef,$delta_ts,$bug_id);
	} else {
		print "There is no date to set for bug $bug_id\n";	
	}
}

print "Migration process has finished successfully!\n";

	
###############################################################################
# Subrutines
###############################################################################

sub update_bug_activity{
	my ($old_name,$new_name) = @_;
	
	# update bugs_activity with the new field id and remove the old ones
	my $fieldid_old = $dbh->selectrow_array("SELECT id from fielddefs where name=?",undef,$old_name);
	# if new_name is empty, just remove the old one
	if ($new_name){
		my $fieldid = $dbh->selectrow_array("SELECT id from fielddefs where name=?",undef,$new_name);
		$dbh->do("UPDATE bugs_activity SET fieldid=? WHERE fieldid = ?",undef,$fieldid,$fieldid_old);
	} else {
		$dbh->do("DELETE FROM bugs_activity WHERE fieldid = ?",undef,$fieldid_old);
	}
	
	$dbh->do("DELETE FROM fielddefs WHERE name=?",undef,$old_name);
}
