#!/usr/bin/perl -T
# -*- Mode: perl; indent-tabs-mode: nil -*-
#
###############################################################################################################################################
#
# Bugzilla utility gives a number of simple function to get and update data on the bugzilla issues
#
# Usage:
# You can use this tool from the browser: 
# 		http://<you server>/bugzilla/utilities.cgi?func=<function name>&<param name>=<param value>&...
#   or using wget from a script, for example:
#		outputfile="/dev/stdout"
#       wget -q -O ${outputfile} "http://<you server>/bugzilla/utilities.cgi?func=<function name>&<param name>=<param value>&..."
# All functions print the answer as a html page.
#
# All function recieve user credentials: as Bugzilla_login and Bugzilla_password
#
# Functions:
# * isStatus - checks if issue or all issues in the given list are in the status X (and in the resolution Y, optional)
# 		parameters:
#			bug_id - existing issue id (mandatory if bug_list is not defined)
#			bug_list - comma separated list of existing issues ids (mandatory if bug_id is not defined)
#			status - valid status name (mandatory)
#			resolution - valid resolution name (optional)
#		returns
#			true - if true
#			empty page - otherwise
#			error message - if parameters are not valid
#		example call
#			 http://<you server>/bugzilla/utilities.cgi?func=isStatus&bug_id=345&status=RESOLVED&resolution=INVALID
#
# * getListByFieldValue - get all issue ids for given list of field=value
# ** NO SUPPORT FOR LIST WITH MULTIVALUED CUSTOM FIELDS AT THE MOMENT **
# 		parameters:
#			bug_id - existing issue id (mandatory)
#			fieldnum - number of the fields (mandatory if more than 1)
#			field(num) - field name as appear in db (in bugs table or customfields table) (mandatory)
#			custom(num) - 1 for custom fields (optional)
#			value(num) - field value to look for
#		returns
#			comma separated list of the issues or error message if parameters are not valid
#		example call
#			 http://<you server>/bugzilla/utilities.cgi?func=getListByFieldValue&field1=found_in_build&value1=200812160915
#			 http://<you server>/bugzilla/utilities.cgi?func=getListByFieldValue&fieldnum=3&field1=product_id&value1=2&field2=found_in_build&value2=200812160915&field3=stam&custom3=1&value3=ttt
#
# * getFieldValue - gets field value from an issue
# 		parameters:
#			bug_id - existing issue id (mandatory)
#			field - field name as appear in db (in bugs table or customfields table) (mandatory)
#			custom - 1 for custom fields (optional)
#		returns
#			field value - for multivalued custom field, the values will appear as is in db (with " " separator) 
#			error message if parameters are not valid
#		example call
#			 http://<you server>/bugzilla/utilities.cgi?func=getFieldValue&bug_id=345&field=cf_found_in_build
#
# * updateFieldValue - updates value of the input field for the input issue. 
#					   can be used for 'non-fuctional' fields only - fields that do not have additional functionality or custom fields
# 		parameters:
#			bug_id - existing issue id (mandatory)
#			changer - existing user that will apear as a changer of an issue (mandatory)
#			field - field name as appear in db (in bugs table or customfields table) (mandatory)
#			value - field value to set 
#					Note: for custom fields - no validation is performed to check if input value is on the defined values list
#						  for multivalued custom fields - the input values will overwrite the exiting ones, so it has to include all values
#														for example: 'value1|value3|value10'
#			custom - 1 for custom fields (optional)
#			append - can be used for custom fields only (optional)
#					 for 'free text' field - if not empty, the input value will be appended to current value (delimited by space)
#					 for 'single select' field - will be ignored
#					 for 'multi select field - if not empty, the input value will be appended to current value
#			max_append - maximum number of values to append (optional)
#						 if set, relevant only for 'free text' field, the oldest value will be removed, "..." will be added to the begining of the value to indicate that old values were removed
#					  
#					
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			 http://<you server>/bugzilla/utilities.cgi?func=updateFieldValue&bug_id=345&field=cf_found_in_build&custom=1&value=200812160915&changer=user1@demo.com
#
# * duplicateProduct - duplicates input product with all its versions,components,target/fixed in versions, modules.
#                      Rest of the new product details will be set to defaults.
#		parameters:
#				product - product name (mandatory)
#				new - new product name (mandatory)
#				desc - product description (optional)
#		returns
#			created product id -  if success
#			error message - otherwise
#		example call
#			 http://<you server>/bugzilla/utilities.cgi?func=duplicateProduct&product=TestProduct&new=NewTestProduct&desc=New%20Test%20Product
#
# * replaceUserCompDef - replaces user X with user Y in components' defaults: default assignee or/and default qa contact or/and default cc
#		parameters:
#			user - existing user login name (mandatory)
#			new_user - existing user Y login name (mandatory)
#			At least one of the following must appear:
#			assignee - true - to replace default assignee in all components 
#			qacontact - true if replace default qa contact in all components 
#			cc - true if replace default cc in all components 
#		returns
#			true -  if success
#			error message - otherwise
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=replaceUserCompDef&user=user1@demo.com&new_user=user2@demo.com&assignee=true
#
# * removeUserFromDefCC - remove user from all his appearances in components' default CC (optional - by product)
#		parameters:
#			user - existing user login name (mandatory)
#			product - existing product name (optional), if defined the user will be removed from defaultCC for components of this product only
#		returns
#			true -  if success
#			error message - otherwise
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=removeUserFromDefCC&user=user1@demo.com&product=XXX
#
# * addUserToDefCC - add user to default CC to all component of the given product
#		parameters:
#			user - existing user login name (mandatory)
#			product - existing product name (mandatory)
#		returns
#			true -  if success
#			error message - otherwise
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=addUserToDefCC&user=user1@demo.com&product=XXX
#
# * createIssue - creates a new issue with input parameters (field=value). There is no validations except mandatory fields!
#		parameters: list of fields (the name must be exact names like in DB), for example
#				product - product name (mandatory)
#				component - component name (mandatory)
#				entity (mandatory)
#				version (mandatory)
#				priority (mandatory)
#				bug_severity (mandatory)
#				op_sys (mandatory)
#				rep_platform (mandatory)
#				reporter - reporter login name (mandatory)
#				assigned_to - assigned_to login name (mandatory)
#				qa_contact - qa_contact login name 
#				short_desc (mandatory)
#				bug_status - if not given, set to NEW
#				resolution
#				comment 
#				parent_bug_id
#				cc - list of cc login names devided by spaces
#		returns
#				created issue id -  if success
#				error message - if any mandatory parameters are missing
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=createIssue&product=TestProduct&component=TestComponent&entity=Bug&version=1.0&rep_platform=PC&priority=P3&severity=normal&reporter=user1@demo.com&assigned_to=user2@demo.com&short_desc=Utility%20test&op_sys=Linux&comment=Created%20automatically%20from%20the%20script&cc=user3@demo.com&cf_target_version=2.0
#
# * updateBugDependencies - updates dependencies of an issue. The list will overwrite the exiting one, so it has to include all dependencies.
#		parameters:
#				bug_id
#				buglist - comma separated list of issues to depend on
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=updateBugDependencies&bug_id=34&buglist=56,78,909
#
# * updateFixedInBuild - updates cf_fixed_in_build field with input value for all issues from the input list that have RESOVED FIXED status
#					NOTE: there is no validation for the bugs list! 
#		parameters:
#			fixed_in_build - build number to set
#			buglist_joined - comma separated list of issues to update
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=updateFixedInBuild&fixed_in_build=BB239&buglist_joined=13044,13127,4934,6413
#
# * addValue2CustomField - adds input value to the list of input custom field values list
#		parameters:
#				field - custom field name (mandatory)
#				value - value to add (mandatory)
#				sortkey - value sortkey (optional)
#				vis_value_id - visibility value id (optional)
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=addValue2CustomField&field=cf_found_in_build&value=2009.4.55
#
# * addValue2CustomFieldDescSortkey - adds input value to the list of input custom field values list while sortky will be the min(sortkey)-1
#									 (used for creating values list in descending order)
#		parameters:
#				field - custom field name (mandatory)
#				value - value to add (mandatory)
#				vis_value_id - visibility value id (optional)
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=addValue2CustomFieldDescSortkey&field=cf_found_in_build&value=2009.4.55
#
# * updateStatusResolution - updates status and resolution for all issues from the input list
#		parameters:
#			status - status to set (mandatory)
#			resolution - resolution to set (mandatory for non-open statuses)
#			buglist - comma separated list of issues to update
#			changer - existing user that will apear as a changer of an issue (mandatory)
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=updateStatusResolution&status=RESOLVED&resolution=FIXED&buglist=13044,13127,4934,6413
#
# * updateStatusResolutionAssignee - updates status, resolution and assignee for all issues from the input list
#		parameters:
#			status - status to set (mandatory)
#			resolution - resolution to set (mandatory for non-open statuses)
#			assigned_to - assigned_to login name (mandatory)
#			buglist - comma separated list of issues to update
#			changer - existing user that will apear as a changer of an issue (mandatory)
#		returns
#			true - if update succeeded
#			error message - if parameters are not valid
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=updateStatusResolutionAssignee&status=RESOLVED&resolution=FIXED&assigned_to=user1@demo.com&buglist=13044,13127,4934,6413
#
# * getAttachmentForBug
# * getLastIdForEntityComponent
# * getLastIdForPatch
# * getComponentsIdTable
#
# * getBugList4Readme - customer specific: performs a few checks on the input issues list and creates updated list in simple text format 
#		parameters:
#			buglist - list of issues (mandatory)
#			fixed_version - the name of the fixed version (mandatory)
#			code_review_bugs - the list of bugs for code_review
#		returns
#			the updated formatted list
#		example call
#			http://<you server>/bugzilla/utilities.cgi?func=getBugList4Readme&buglist=13044,13127,4934,6413&fixed_version=XXX&code_review_bugs=13127,4934
#
#
####################################################################################################################################################

#use strict; 
use warnings;

use lib ".";

use Bugzilla;
use Bugzilla::Bug;
use Bugzilla::Constants;
use Bugzilla::Field;
use Bugzilla::Util;
use Bugzilla::Error;

my $dbh = Bugzilla->dbh;
my $cgi = Bugzilla->cgi;


print "Content-type: text/html\n\n"; 


my $function = $cgi->param('func') || "";

# First, record if Bugzilla_login and Bugzilla_password were provided
my $credentials_provided=0;
if (defined($cgi->param('Bugzilla_login')) && defined($cgi->param('Bugzilla_password'))){
    $credentials_provided = 1;
}
# Next, log in the user
if ($credentials_provided) {
	Bugzilla->login(LOGIN_REQUIRED);
} else {
	Bugzilla->login();
}

# bug fields list
my @issue_fields = Bugzilla::Bug->DB_COLUMNS;

# custom fields
my @custom_multi = map { $_->name }  (grep {$_->type == FIELD_TYPE_MULTI_SELECT} Bugzilla->active_custom_fields);
my @custom_single = map { $_->name }  (grep {$_->type == FIELD_TYPE_SINGLE_SELECT} Bugzilla->active_custom_fields);
my @custom_freetext = map { $_->name }  (grep {$_->type == FIELD_TYPE_FREETEXT} Bugzilla->active_custom_fields);
                      
# functional fields
my @ffields = ("bug_status","resolution","assigned_to","qa_contact",
				"component_id","reporter","version", "product_id",
				"parent_bug_id","resolver","entity","reopen_resolution");


# functions						
if ($function eq "isStatus") {
	
	my $bug_id = $cgi->param('bug_id') || "";
	my $bug_list = $cgi->param('bug_list') || ""; # comma separated list expected
	my $status = $cgi->param('status') || "";
	my $resolution = $cgi->param('resolution') || "";
	
	# validation
	if ($status eq "" || ($bug_id eq "" && $bug_list eq "")){
		print "status and bug_id/bug_list parameters can not be empty!";
		exit 1;
	} 
	
	trick_taint($bug_id);
	trick_taint($bug_list);
	trick_taint($status);
	trick_taint($resolution);
	
	my $res;
	if ($bug_id ne "") { # for single issue
		if ($resolution ne ""){
			$res = $dbh->selectrow_array("SELECT true FROM bugs WHERE bug_id=? AND bug_status=? AND resolution=?", undef, $bug_id, $status, $resolution);
		} else {
			$res = $dbh->selectrow_array("SELECT true FROM bugs WHERE bug_id=? AND bug_status=?", undef, $bug_id, $status);
		}
	} else { # for list of issues
		my @list = split(/,/,$bug_list);
		if ($resolution ne ""){
			$res = 1;
			foreach my $b (@list){
				$res = $dbh->selectrow_array("SELECT true FROM bugs WHERE bug_id=? AND bug_status=? AND resolution=?", undef, $b, $status, $resolution);
				if ($res == 0 ){
					last; #no point to continue
				}			
			}
			
		} else {
			$res = 1;
			foreach my $b (@list){
				$res = $dbh->selectrow_array("SELECT true FROM bugs WHERE bug_id=? AND bug_status=?", undef, $b, $status);
				if ($res == 0 ){
					last; #no point to continue
				}			
			}
			
		}
	}
	if ($res == 1){
		print "true";
	} else {
		print "false";
	}
	
} elsif ($function eq "getListByFieldValue") {
	
	my $fieldnum = $cgi->param('fieldnum') || 1;
	
	if ($fieldnum == 1){
		my $field = $cgi->param('field1') || "";
		my $value = $cgi->param('value1') || "";
		my $custom = $cgi->param('custom1') || ""; # 1 - for custom field expected
		if ($field eq "" ){
			print "field parameter can not be empty!";
			exit 1;
		} 
		
		trick_taint($field);
		trick_taint($custom);
		trick_taint($value);
		
		my $list = "";
		if ($custom eq "1" && lsearch(\@custom_multi, $field) >= 0){
			# if field is multi valued
			my $list_ref = $dbh->selectcol_arrayref("SELECT bug_id FROM bug_$field WHERE value= ?", undef, $value );
			$list = join(",",@$list_ref);
			print $list;
		} else {
			# check if the field is on the list
			if (lsearch(\@issue_fields, $field) >= 0){
				my $list_ref = $dbh->selectcol_arrayref("SELECT bug_id FROM bugs WHERE $field= ?", undef, $value );
				$list = join(",",@$list_ref);
				print $list;
			} else {
				print "Field '$field' is not on the fields list";
				exit 1;
			}
		}
		
	} elsif ($fieldnum > 1){
		my @mfields;
		my @mcfields;
		
		my $query = "SELECT bug_id FROM bugs WHERE ";
		
		my $field = $cgi->param('field1') || "";
		my $value = $cgi->param('value1') || "";
		my $custom = $cgi->param('custom1') || ""; # 1 - for custom field expected
		
		if ($custom eq "1" && lsearch(\@custom_multi, $field) >= 0){
			print "NO SUPPORT FOR LIST WITH MULTIVALUED CUSTOM FIELDS AT THE MOMENT!";
			exit 1;
		}
		
		trick_taint($field);
		trick_taint($custom);
		trick_taint($value);
	
		if (lsearch(\@issue_fields, $field) >= 0){
			$query .= $field." = '".$value."' ";
		} else {
			print "Field '$field' is not on the fields list";
			exit 1;
		}
		
		for (my $i = 2; $i <= $fieldnum; $i++){
			$field = $cgi->param('field'.$i) || "";
			$value = $cgi->param('value'.$i) || "";
			$custom = $cgi->param('custom'.$i) || ""; # 1 - for custom field expected
			
			if ($custom eq "1" && lsearch(\@custom_multi, $field) >= 0){
				print "NO SUPPORT FOR LIST WITH MULTIVALUED CUSTOM FIELDS AT THE MOMENT!";
				exit 1;
			}
			
			trick_taint($field);
			trick_taint($custom);
			trick_taint($value);
		
			if (lsearch(\@issue_fields, $field) >= 0){
				$query .= "AND ".$field." = '".$value."' ";
			} else {
				print "Field '$field' is not on the fields list";
				exit 1;
			}
		}
		my $list_ref = $dbh->selectcol_arrayref($query);
		my $list = join(",",@$list_ref);
		print $list;
	}
	
} elsif ($function eq "getFieldValue") {
	
	my $field = $cgi->param('field') || "";
	my $bug_id = $cgi->param('bug_id') || "";
	
	# validations
	if ($field eq "" || $bug_id eq ""){
		print "getFieldValue - field and bug_id parameters can not be empty! (fileld=$field bug_id=$bug_id)";
		exit 1;
	} 
	
	trick_taint($bug_id);
	trick_taint($field);
	
	my $value = "";
	# check if the field is on the list
	if (lsearch(\@issue_fields, $field) || lsearch(\@custom_multi, $field) ){
		$value = $dbh->selectrow_array("SELECT $field FROM bugs WHERE bug_id = ? ", undef, $bug_id);
	} else {
		print "Field '$field' is not on the fields list";
		exit 1;
	}
	print $value;
	
} elsif ($function eq "getComponentForIssue") {

	my $bug_id = $cgi->param('bug_id') || "";

	# validations
	if ($bug_id eq ""){
		print "bug_id can not be empty!";
		exit 1;
	}

	trick_taint($bug_id);

	my $component_id = $dbh->selectrow_array("SELECT component_id FROM bugs WHERE bug_id = ? ", undef, $bug_id);
	print $component_id;

} elsif ($function eq "updateFieldValue") {
	
	my $field = $cgi->param('field') || "";
	my $value = $cgi->param('value') || "";
	my $custom = $cgi->param('custom') || ""; # 1 - for custom field expected
	my $bug_id = $cgi->param('bug_id') || "";
	my $changer = $cgi->param('changer') || "";
	my $append = $cgi->param('append') || "";
	my $max_append = $cgi->param('max_append') || "";
	
	# validations
	if ($field eq "" || $bug_id eq "" || $changer eq ""){
		print "updateFieldValue - changer, field and bug_id parameters can not be empty!";
		exit 1;
	} 
		
	trick_taint($bug_id);
	trick_taint($field);
	trick_taint($custom);
	trick_taint($value);
	trick_taint($changer);
	trick_taint($append);
	trick_taint($max_append);
	
	my $user = Bugzilla::User->new({ name => $changer })
    || ThrowUserError('invalid_username', { name => $changer });
	Bugzilla->set_user($user);
	
	my $old_value;
	my $updated = 0;
	
	$dbh->bz_start_transaction();
	
	if ($custom eq "1" && lsearch(\@custom_multi, $field) >= 0){
		# check if the field is on the list
		$old_value = $dbh->selectrow_array("SELECT $field FROM bugs WHERE bug_id = ?", undef, $bug_id);
		$value =~ s/\|/ /;
		if ($old_value ne $value) {
			if ($append && $old_value ne ""){
				if ( index($old_value, $value) < 0){
					$value = $old_value." ".$value;
				} else {
					$value = $old_value;
				}
			}
			my @values = split (/\s/,$value); 
			$dbh->do("DELETE FROM bug_$field WHERE bug_id = ?", undef, $bug_id);
			foreach my $v (@values){
				$dbh->do("INSERT INTO bug_$field (value,bug_id) VALUES(?,?)", undef, $v, $bug_id);
			}
			$dbh->do("UPDATE bugs SET $field=? where bug_id=?",undef, $value, $bug_id);	
			$updated = 1;
		}
		
	} else {
		# check if the field is on the list
		if (lsearch(\@issue_fields, $field) >= 0){
			# check that the field is not one of the functional ones
			if (lsearch(\@ffields, $field) < 0) {
				$old_value = $dbh->selectrow_array("SELECT $field FROM bugs WHERE bug_id = ? ", undef, $bug_id);
				if ($old_value ne $value) {
					if ($append && lsearch(\@custom_freetext, $field) >= 0 && $old_value ne ""){
						if ( index($old_value, $value) < 0){
							# check if number of existing values is maximum
							my @novalues = split (" ",$old_value);
							if (@novalues >= $max_append){
								if ($novalues[0] eq "..."){
									shift @novalues;
								}
								shift @novalues;
								$old_value = "... ".join(" ",@novalues);
							}
							$value = $old_value." ".$value;
							$dbh->do("UPDATE bugs SET $field = ? WHERE bug_id = ?", undef, $value, $bug_id);
							$updated = 1;
						}
					} else { 
						$dbh->do("UPDATE bugs SET $field = ? WHERE bug_id = ?", undef, $value, $bug_id);
						$updated = 1;
					} 
				}
			} else {
				print "This field ($field) is a functional field, con not be updated";
			}
		} else {
			print "Field '$field' is not on the fields list";
		}
	}
	if ($updated == 1){
		$old_value = "" if (!$old_value);
		my $timestamp = $dbh->selectrow_array(q{SELECT NOW()});
		LogActivityEntry( $bug_id, $field, $old_value, $value, $user->id, $timestamp );
	}
	
	$dbh->bz_commit_transaction();
	print "true";	

} elsif ($function eq "duplicateProduct"){
	
	my $product = $cgi->param('product') || "";
	my $new_product = $cgi->param('new') || "";
	my $desc = $cgi->param('desc') || "";
	
	# validations
	if ($product eq "" || $new_product eq ""){
		print "product and new product names can not be empty!";
		exit 1;
	} 
		
	trick_taint($product);
	trick_taint($new_product);
	trick_taint($desc);
	
	my ($product_id,$class_id,$def_milestone) = $dbh->selectrow_array( "SELECT id, classification_id, defaultmilestone from products WHERE name=?", undef, $product);
	if (!$product_id){
		print "product $product does not exist!";
		exit 1;
	}
	
	# create product
	$dbh->bz_start_transaction();
	$dbh->do("INSERT INTO products(name, description, defaultmilestone, classification_id,
                           disallownew, votesperuser, votestoconfirm, showonhomepage)
               		VALUES (?, ?, ?, ?, 0, 0, 0, 1)",
               undef, $new_product, $desc, $def_milestone,$class_id);
               
    my $new_product_id = $dbh->bz_last_key('products', 'id');
	
	# components
	$dbh->do("INSERT INTO components(name, product_id, description, initialowner,
									initialqacontact, invisible)
               	SELECT name, ?, description, initialowner, initialqacontact, invisible
               	    FROM components 
					WHERE product_id=$product_id",
               undef, $new_product_id);
               
	# versions
	$dbh->do("INSERT INTO versions(value, product_id, status)
               	SELECT value, ?, status
               	    FROM versions 
					WHERE product_id=$product_id",
               undef, $new_product_id);

	# target versions
	$dbh->do("INSERT INTO milestones(value, product_id, invisible, sortkey)
               	SELECT value, ?, invisible, sortkey
               	    FROM milestones 
					WHERE product_id=$product_id",
               undef, $new_product_id);

#    use Bugzilla::Config qw(:DEFAULT $datadir);
#    # Make versioncache flush
#    unlink "$datadir/versioncache";  

	$dbh->bz_commit_transaction();  
               
    print $new_product_id;      
    
} elsif ($function eq "replaceUserCompDef"){
	
	my $user = $cgi->param('user') || "";
	my $new_user = $cgi->param('new_user') || "";
	my $assignee = $cgi->param('assignee') || "";
	my $qacontact = $cgi->param('qacontact') || "";
	my $cc = $cgi->param('cc') || "";
	
	# check that users are valid and get their ids
	trick_taint($user);
	trick_taint($new_user);
	my $user_id = $dbh->selectrow_array( "SELECT userid from profiles WHERE login_name=?", undef, $user);
	my $new_user_id = $dbh->selectrow_array( "SELECT userid from profiles WHERE login_name=?", undef, $new_user);
	if (!$user || !$new_user_id){
		print "user and new_user are mandatory parameters!\n";
		exit 1;
	}
	if ($assignee eq "" && $qacontact eq "" && $cc eq ""){
		print "At list one of the parameters - assignee, qacontact or cc, - must appear!\n";
		exit 1;
	}
	
	if ($assignee eq "true"){
		$dbh->do("UPDATE components SET initialowner=? where initialowner=? ",undef,$new_user_id, $user_id);
	}
	if ($qacontact eq "true"){
		$dbh->do("UPDATE components SET initialqacontact=? where initialqacontact=? ",undef,$new_user_id, $user_id);
	}
	if ($cc eq "true"){
		
		# get the list of components where old user appears
		my $comp_ids = $dbh->selectcol_arrayref("SELECT component_id FROM component_cc WHERE user_id=?",undef,$user_id);
		
		# delete old user from initial cc
		$dbh->do("DELETE FROM component_cc WHERE user_id=?",undef,$user_id);
		
		# add new user to initial cc
		foreach my $comp_id (@$comp_ids){
			$dbh->do("INSERT INTO component_cc (component_id,user_id)  VALUES (?,?)",undef,$comp_id,$new_user_id);
		}

	}
	
	print "true";
	
} elsif ($function eq "removeUserFromDefCC"){
	
	my $user = $cgi->param('user') || "";
	my $product = $cgi->param('product') || "";
	
	if ($user eq ""){
		print "user is a mandatory parameter!\n";
		exit 1;
	}
	
	# check that user is valid and get its id
	trick_taint($user);
	my $user_id = $dbh->selectrow_array( "SELECT userid from profiles WHERE login_name=?", undef, $user);
	if (!$user_id ){
		print "Input user has to be a valid exiting user login!\n";
		exit 1;
	}
	
	if ($product ne ""){
		trick_taint($product);
		my $product_id = $dbh->selectrow_array( "SELECT id from products WHERE name=?", undef, $product);
		if (!$product_id){
			print "product $product does not exist!";
			exit 1;
		}
		# delete old user from initial cc
		$dbh->do("DELETE FROM component_cc WHERE user_id=? AND component_id in (SELECT id FROM components WHERE product_id=?)",undef,$user_id,$product_id);
	} else {
		# delete old user from initial cc
		$dbh->do("DELETE FROM component_cc WHERE user_id=?",undef,$user_id);
	}
	
	print "true";
	
} elsif ($function eq "addUserToDefCC"){
	
	my $user = $cgi->param('user') || "";
	my $product = $cgi->param('product') || "";
	
	if ($user eq "" || $product eq ""){
		print "user and product are mandatory parameters!\n";
		exit 1;
	}
	
	# check that user is valid and get its id
	trick_taint($user);
	my $user_id = $dbh->selectrow_array( "SELECT userid from profiles WHERE login_name=?", undef, $user);
	if (!$user_id ){
		print "Input user has to be a valid exiting user login!\n";
		exit 1;
	}
	
	trick_taint($product);
	my $product_id = $dbh->selectrow_array( "SELECT id from products WHERE name=?", undef, $product);
	if (!$product_id){
		print "product $product does not exist!";
		exit 1;
	}
	# add user to initial cc for input product
	my $component_ids = $dbh->selectcol_arrayref("SELECT id FROM components WHERE product_id=? ",undef,$product_id);
    foreach my $comp_id ( @$component_ids ) {
    	$dbh->do("INSERT INTO component_cc (user_id,component_id) VALUES (?,?)",undef,$user_id,$comp_id);
	}	
	
	print "true";
	
} elsif ($function eq "createIssue"){
	
	my $reporter = $cgi->param('reporter') || "";
	if (!$reporter){
		print "Reporter can not be empty!";
		exit 1;
	}
	my $user = Bugzilla::User->new({ name => $reporter })
    || ThrowUserError('invalid_username', { name => $reporter });
	Bugzilla->set_user($user);
	
	Bugzilla->usage_mode(USAGE_MODE_EMAIL);
	
    require 'post_bug.cgi';
	
} elsif ($function eq "updateBugDependencies"){
	my $bug_id = $cgi->param('bug_id') || "";
	my $buglist = $cgi->param('buglist') || "";

	# validations
	if ($bug_id eq "" || $buglist eq ""){
		print "bug_id and buglist can not be empty!";
		exit 1;
	}

	trick_taint($bug_id);
	trick_taint($buglist);
	
	$dbh->bz_start_transaction();

	my @list = split(/,/,$buglist);
	$dbh->do("DELETE from dependencies WHERE blocked=?",undef,$bug_id);
	foreach my $b (@list){
		$dbh->do("INSERT INTO dependencies (blocked, dependson) VALUES (?, ?)",undef, $bug_id, $b);
	}
	print "true";
	
	$dbh->bz_commit_transaction();

} elsif ($function eq "getAttachmentForBug"){
	my $bug_id = $cgi->param('bug_id') || "";
	my $file_name = $cgi->param('file_name') || "";

	# validations
	if ($bug_id eq ""){
		print "bug_id can not be empty!";
		exit 1;
	}

	trick_taint($bug_id);
	trick_taint($file_name);

	my $value = "";
	if($file_name eq "") {
		$value = $dbh->selectrow_array("SELECT thedata FROM attach_data JOIN attachments ON attachments.attach_id=attach_data.id WHERE attachments.bug_id=?", undef, $bug_id);
	} else {
		$value = $dbh->selectrow_array("SELECT thedata FROM attach_data JOIN attachments ON attachments.attach_id=attach_data.id WHERE attachments.bug_id=? and attachments.filename=?", undef, $bug_id, $file_name);
	}
	print $value;

} elsif ($function eq "getLastIdForEntityComponent") {

	my $entity_type = $cgi->param('entity_type') || "";
	my $component = $cgi->param('component') || "";
	my $version = $cgi->param('version') || "";

	# validations
	if ($entity_type eq "" || $component eq "" || $version eq ""){
		print "getLastIdForEntityComponent - entity_type, component and version parameters can not be empty!";
		exit 1;
	}

	trick_taint($entity_type);
	trick_taint($component);
	trick_taint($version);

	my $value = "";
	my $component_id = $dbh->selectrow_array( "SELECT id from components WHERE name=?", undef, $component);
	$value = $dbh->selectrow_array("SELECT bug_id FROM bugs WHERE entity='$entity_type' and version='$version' and component_id=$component_id order by bug_id DESC limit 1", undef);
	print $value;
	
} elsif ($function eq "getLastIdForPatch") {

	my $component = $cgi->param('component') || "";
	my $version = $cgi->param('version') || "";
	my $target_patch = $cgi->param('target_patch') || "";

	# validations
	if ($target_patch eq "" || $component eq "" || $version eq ""){
		print "getPreviousIdForPatch - target_patch, component and version parameters can not be empty!";
		exit 1;
	}

	trick_taint($target_patch);
	trick_taint($component);
	trick_taint($version);

	my $value = "";
	my $component_id = $dbh->selectrow_array( "SELECT id from components WHERE name=?", undef, $component);

	$value = $dbh->selectrow_array("SELECT bug_id FROM bugs WHERE entity='Patch' and version=? and component_id=? and cf_target_patch=? order by bug_id DESC limit 1", undef, $version, $component_id, $target_patch);
	print $value;

} elsif ($function eq "getComponentsIdTable") {
	my $list_ref = $dbh->selectall_arrayref("SELECT id,name FROM components");
    foreach my $ref ( @$list_ref ) {
    	print join(",",@$ref)."\n";
	}	
	
} elsif ($function eq "updateFixedInBuild"){
	my $fixed_in_build = $cgi->param('fixed_in_build') || "";
	my $buglist_joined = $cgi->param('buglist_joined') || "";
	
	# validations
	if (lsearch(\@issue_fields, "cf_fixed_in_build") < 0){
		print "Field 'cf_fixed_in_build' is not on the fields list";
		exit 1;
	}
	if ($fixed_in_build eq ""){
		print "updateFixedInBuild - fixed_in_build parameter can not be empty!";
		exit 1;
	}
	
	if ($buglist_joined ne ""){
		
		trick_taint($fixed_in_build);
		trick_taint($buglist_joined);
		
		my $filtered_bug_list = $dbh->selectcol_arrayref("SELECT bug_id FROM bugs WHERE bug_status='RESOLVED' AND resolution='FIXED' AND bug_id IN ($buglist_joined)");
		my $updated_bugs = join(',',@$filtered_bug_list);
		if ($updated_bugs ne ""){
			$dbh->do("UPDATE bugs SET cf_fixed_in_build=? WHERE bug_id IN ($updated_bugs)",undef,$fixed_in_build);	
			print "Success - updated bugs [$updated_bugs]";
		} else {
			print "There is no bugs to update";
		}
		
	} else {
		print "There is no bugs to update";
	}

} elsif ($function eq "updateStatusResolution"){
	my $status = $cgi->param('status') || "";
	my $resolution = $cgi->param('resolution') || "";
	my $buglist = $cgi->param('buglist') || "";
	my $changer = $cgi->param('changer') || "";
	
	# validations
	if ($status eq "" || $changer eq ""){
		print "updateStatusResolution - changer and status parameter can not be empty!";
		exit 1;
	}
	use Bugzilla::Status;
	my $is_open = is_open_state($status);
	if (!$is_open && $resolution eq ""){
		print "updateStatusResolution - resolution parameter can not be empty for a non-open status($status)!";
		exit 1;
	}
	
	if ($buglist ne ""){
		
		trick_taint($status);
		trick_taint($resolution) if ($resolution ne "");
		trick_taint($buglist);
		trick_taint($changer);
	
		my $user = Bugzilla::User->new({ name => $changer })
	    || ThrowUserError('invalid_username', { name => $changer });
		Bugzilla->set_user($user);
		
		foreach my $bug_id (split (",",$buglist)){
			my $bug = Bugzilla::Bug->check($bug_id);
			$dbh->bz_start_transaction();
			$bug->set_status($status, {resolution => $resolution,});
			$bug->update();			
			$dbh->bz_commit_transaction();
		}
		print "true";
	}
	
} elsif ($function eq "updateStatusResolutionAssignee"){
	my $status = $cgi->param('status') || "";
	my $resolution = $cgi->param('resolution') || "";
	my $buglist = $cgi->param('buglist') || "";
	my $changer = $cgi->param('changer') || "";
	my $assigned_to = $cgi->param('assigned_to') || "";
	
	# validations
	if ($status eq "" || $changer eq "" || $assigned_to eq ""){
		print "updateStatusResolutionAssignee - changer, assigned_to and status parameters can not be empty!";
		exit 1;
	}
	use Bugzilla::Status;
	my $is_open = is_open_state($status);
	if (!$is_open && $resolution eq ""){
		print "updateStatusResolutionAssignee - resolution parameter can not be empty for a non-open status($status)!";
		exit 1;
	}
	
	if ($buglist ne ""){
		
		trick_taint($status);
		trick_taint($resolution) if ($resolution ne "");
		trick_taint($buglist);
		trick_taint($changer);
		trick_taint($assigned_to);
	
		my $assignee = Bugzilla::User->new({ name => $assigned_to })
	    || ThrowUserError('invalid_username', { name => $assigned_to });
		my $user = Bugzilla::User->new({ name => $changer })
	    || ThrowUserError('invalid_username', { name => $changer });
		Bugzilla->set_user($user);
		
		foreach my $bug_id (split (",",$buglist)){
			my $bug = Bugzilla::Bug->check($bug_id);
			$dbh->bz_start_transaction();
			$bug->set_assigned_to($assignee);
			$bug->set_status($status, {resolution => $resolution,});
			$bug->update();			
			$dbh->bz_commit_transaction();
		}
		print "true";
	}


} elsif ($function eq "addValue2CustomField"){
	my $field_name = $cgi->param('field') || "";
	my $value = $cgi->param('value') || "";
	my $sortkey = $cgi->param('sortkey') || 0;
	my $visibility_value_id = $cgi->param('vis_value_id') || "";
	
	# validations
	if ($field_name eq "" || $value eq "" ){
		print "addValue2CustomField - field and value parameters can not be empty!";
		exit 1;
	}
	if (lsearch(\@issue_fields, $field_name) < 0){
		print "Field '$field_name' is not on the fields list";
		exit 1;
	}
	my $field = new Bugzilla::Field({'name' => $field_name});
	if ($field && $field->is_select){
		# check if already exists
		trick_taint($value);
		trick_taint($field_name);
		trick_taint($sortkey);
		trick_taint($visibility_value_id);
		if ($sortkey == 0){
			$sortkey = $dbh->selectrow_array("SELECT max(sortkey) FROM $field_name",undef);
			$sortkey++;
		}
		my $value_test = $dbh->selectrow_array("SELECT value FROM $field_name WHERE value=?",undef,$value);
		if ($value_test){
			print "Value '$value' already exists for field '$field_name'\n";
			exit 1;
		} else {
			my $created_value = Bugzilla::Field::Choice->type($field)->create({
		        value   => $value, 
		        sortkey => $sortkey,
		        is_open => 1,
		        visibility_value_id => $visibility_value_id,
		    });	
		}
		
	} else {
		print "Field '$field_name' is not a SELECT field, can not have predefined values";
		exit 1;
	}
	
	print "true";
	
} elsif ($function eq "addValue2CustomFieldDescSortkey"){
	my $field_name = $cgi->param('field') || "";
	my $value = $cgi->param('value') || "";
	my $visibility_value_id = $cgi->param('vis_value_id') || "";
	
	# validations
	if ($field_name eq "" || $value eq "" ){
		print "addValue2CustomFieldDescSortkey - field and value parameters can not be empty!";
		exit 1;
	}
	if (lsearch(\@issue_fields, $field_name) < 0){
		print "Field '$field_name' is not on the fields list";
		exit 1;
	}
	my $field = new Bugzilla::Field({'name' => $field_name});
	if ($field && $field->is_select){
		# check if already exists
		trick_taint($value);
		trick_taint($field_name);
		trick_taint($visibility_value_id);
		my $value_test = $dbh->selectrow_array("SELECT value FROM $field_name WHERE value=?",undef,$value);
		if ($value_test){
			print "Value '$value' already exists for field '$field_name'\n";
			exit 1;
		} else {
			my	$sortkey = $dbh->selectrow_array("SELECT min(sortkey) FROM $field_name",undef);
		   $sortkey--;
			my $created_value = Bugzilla::Field::Choice->type($field)->create({
		        value   => $value, 
		        sortkey => $sortkey,
		        is_open => 1,
		        visibility_value_id => $visibility_value_id,
		    });	
		}
		
	} else {
		print "Field '$field_name' is not a SELECT field, can not have predefined values";
		exit 1;
	}
	
	print "true";
	
} elsif ($function eq "getBugList4Readme"){
	my $buglist = $cgi->param('buglist') || "";
	my $fixed_version = $cgi->param('fixed_version') || "";
	my $code_review_bugs = $cgi->param('code_review_bugs') || "";
	
	trick_taint($buglist);
	my $newbuglist = $dbh->selectall_arrayref("SELECT bug_id,crm,short_desc,bug_status,entity,cf_target_version FROM bugs WHERE bug_id IN ($buglist) ORDER BY short_desc", undef);
	foreach my $bug (@$newbuglist) {
        my ($bug_id,$crm,$short_desc,$bug_status,$entity,$target_version) = @$bug;
        my @tv = join(" ",$target_version);
        my $notfixed = 0;
        # if fixed version does not appear in the target versions list
        if ($fixed_version ne "" && (grep { $_->[0] eq $fixed_version } @tv)){
        	$notfixed = 1;
        }
        if ($entity ne "Bug" && $entity ne "Wish" && $entity ne "Feature"){
        	$bug_id = "**".$bug_id;
        } elsif ($bug_status eq "NEW" || $bug_status eq "ASSIGNED" || $bug_status eq "REOPENED"){
    		$bug_id = "*".$bug_id;
    	} elsif ($notfixed){
    		$bug_id = "***".$bug_id;
    	} elsif ($code_review_bugs ne "" && $code_review_bugs =~ m/^($bug_id),|,($bug_id),|,($bug_id)$/){
    		$bug_id = "****".$bug_id;
    	}
    	if ($crm ne ""){
    		$tmpcrm = "";
    		my @tmplst = split( / /, $crm );
			foreach my $c (@tmplst) {
				$c =~ s/^0+//ig;
				$tmpcrm .= $c . ",";
			}
			$tmpcrm =~ s/,$//i;
			$crm = $tmpcrm;
			if ( scalar(@tmplst) == 1 ) { $crm .= "\t"; }
    	} else {
    		$crm = "    \t";
    	}
    	print $bug_id."\t".$crm."\t".$short_desc."\n";
    	
	}
		
} else {
	print "Unknown function $function";
}
