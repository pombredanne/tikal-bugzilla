#!/usr/bin/perl -wT
# -*- Mode: perl; indent-tabs-mode: nil -*-
#

use strict;

use lib qw(. lib);

use Bugzilla;
use Bugzilla::Constants;
use Bugzilla::User;
use Bugzilla::Browse;
use Bugzilla::Classification;
use Bugzilla::Product;
use Bugzilla::Util;
use Bugzilla::Menu;

use vars qw(
  $template
  $vars
);

my $cgi = Bugzilla->cgi;
my $template = Bugzilla->template;

my $user = Bugzilla->login(LOGIN_REQUIRED);

$vars = Bugzilla::Menu::PopulateClassificationAndProducts();

my $userid = Bugzilla->user->id;
my $action = trim($cgi->param('action') || '');

my $product_name = trim($cgi->param('product') || '');
my $product;
my $classification_name = Bugzilla->params->{'useclassification'} ? scalar($cgi->param('classification')) : '__all';

if ($product_name eq '' && $action eq '') {
    # If the user cannot enter bugs in any product, stop here.
    my @selectable_products = @{$user->get_selectable_products};
    ThrowUserError('no_products') unless scalar(@selectable_products);

    # Unless a real classification name is given, we sort products
    # by classification.
    my @classifications;

    unless ($classification_name && $classification_name ne '__all') {
        if (Bugzilla->params->{'useclassification'}) {
            my $class;
            # Get all classifications with at least one selectable product.
            foreach my $product (@selectable_products) {
                $class->{$product->classification_id}->{'object'} ||=
                    new Bugzilla::Classification($product->classification_id);
                # Nice way to group products per classification, without querying
                # the DB again.
                push(@{$class->{$product->classification_id}->{'products'}}, $product);
            }
            @classifications = sort {$a->{'object'}->sortkey <=> $b->{'object'}->sortkey
                                     || lc($a->{'object'}->name) cmp lc($b->{'object'}->name)}
                                    (values %$class);
        }
        else {
            @classifications = ({object => undef, products => \@selectable_products});
        }
    }

    unless ($classification_name) {
        # We know there is at least one classification available,
        # else we would have stopped earlier.
        if (scalar(@classifications) > 1) {
            # We only need classification objects.
            $vars->{'classifications'} = [map {$_->{'object'}} @classifications];

            $vars->{'target'} = "browse.cgi";
            $vars->{'format'} = $cgi->param('format');

            print $cgi->header();
            $template->process("global/choose-classification.html.tmpl", $vars)
               || ThrowTemplateError($template->error());
            exit;
        }
        # If we come here, then there is only one classification available.
        $classification_name = $classifications[0]->{'object'}->name;
    }

    # Keep only enterable products which are in the specified classification.
    if ($classification_name ne "__all") {
        my $class = new Bugzilla::Classification({'name' => $classification_name});
        # If the classification doesn't exist, then there is no product in it.
        if ($class) {
            @selectable_products
              = grep {$_->classification_id == $class->id} @selectable_products;
            @classifications = ({object => $class, products => \@selectable_products});
        }
        else {
            @selectable_products = ();
        }
    }

    if (scalar(@selectable_products) == 0) {
        ThrowUserError('no_products');
    }
    elsif (scalar(@selectable_products) > 1) {
        $vars->{'classifications'} = \@classifications;
        $vars->{'target'} = "browse.cgi";
        $vars->{'format'} = $cgi->param('format');

        print $cgi->header();
        $template->process("global/choose-product.html.tmpl", $vars)
          || ThrowTemplateError($template->error());
        exit;
    } else {
        # Only one product exists.
        $product = $selectable_products[0];
    }
}
else {
    # Do not use Bugzilla::Product::check_product() here, else the user
    # could know whether the product doesn't exist or is not accessible.
    $product = new Bugzilla::Product({'name' => $product_name});
}

if ($action eq '') {
	$action = "browse";
}

$vars->{'action'} = $action;
$vars->{'classification'} = $classification_name;

$vars->{'product'} = $product_name;
my @browse_list;
my $window1;
my $window2;
my $window3;
my $window4;
my $window5;

#
# action='browse_product' -> present the browse for selected product
#
if ($action eq 'browse') {

	if ($product) { # browse for product

		# TODO - add a check if user is allowed to see the product
        $vars->{'product_url'} = $product->milestone_url;
		$vars->{'product_desc'} = $product->description;

		@browse_list = Bugzilla::Browse::GetBrowseDef(1);
		$vars->{'browse_list'} = \@browse_list;

		# build the result for each window
		$window1 = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[0] {'bugs_field_name'}, $browse_list[0] {'table_name'}, $browse_list[0] {'field_name'}, 	$browse_list[0] {'key_field_name'});
		$window2 = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[1] {'bugs_field_name'}, $browse_list[1] {'table_name'}, $browse_list[1] {'field_name'}, $browse_list[1] {'key_field_name'});
		$window3 = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[2] {'bugs_field_name'}, $browse_list[2] {'table_name'}, $browse_list[2] {'field_name'}, $browse_list[2] {'key_field_name'});
		$window4 = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[3] {'bugs_field_name'}, $browse_list[3] {'table_name'}, $browse_list[3] {'field_name'}, $browse_list[3] {'key_field_name'});
		if (scalar(@browse_list) == 5){
			$window5 = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[4] {'bugs_field_name'}, $browse_list[4] {'table_name'}, $browse_list[4] {'field_name'}, $browse_list[4] {'key_field_name'});	
			$vars->{'5'} = $window5;
		}
		
		$vars->{'title'} = "Browse ".Bugzilla->params->{"product_field_name"};
		$vars->{'1'} = $window1;
		$vars->{'2'} = $window2;
		$vars->{'3'} = $window3;
		$vars->{'4'} = $window4;

		# get totals
		$vars->{'total_opened'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'NEW','ASSIGNED','REOPENED'");
		$vars->{'total_resolved'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'RESOLVED','VERIFIED'");
		$vars->{'total_closed'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'CLOSED'");

		print $cgi->header();
	    $template->process("browse/browse-product.html.tmpl", $vars)
		        	|| ThrowTemplateError($template->error());
	    exit;

	} else { 	# browse for classification

		@browse_list = Bugzilla::Browse::GetBrowseDef(2);
		$vars->{'browse_list'} = \@browse_list;

		# get the list of the products ids
		my $classification = new Bugzilla::Classification({'name' => $classification_name});

 		my $products_list = "";
 		my $products = $classification->products;
		foreach my $p (@$products) {
			$products_list .= $p->id.",";
		}
		if ($products_list ne "") {
			chop $products_list;
		}

		# build the result for each window
		$window1 = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[0] {'bugs_field_name'}, $browse_list[0] {'table_name'}, $browse_list[0] {'field_name'}, 	$browse_list[0] {'key_field_name'});
		$window2 = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[1] {'bugs_field_name'}, $browse_list[1] {'table_name'}, $browse_list[1] {'field_name'}, $browse_list[1] {'key_field_name'});
		$window3 = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[2] {'bugs_field_name'}, $browse_list[2] {'table_name'}, $browse_list[2] {'field_name'}, $browse_list[2] {'key_field_name'});
		$window4 = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[3] {'bugs_field_name'}, $browse_list[3] {'table_name'}, $browse_list[3] {'field_name'}, $browse_list[3] {'key_field_name'});
		if (scalar(@browse_list) == 5){
			$window5 = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[4] {'bugs_field_name'}, $browse_list[4] {'table_name'}, $browse_list[4] {'field_name'}, $browse_list[4] {'key_field_name'});
			$vars->{'5'} = $window5;
		}
		
		$vars->{'title'} = "Browse Classification";
		$vars->{'1'} = $window1;
		$vars->{'2'} = $window2;
		$vars->{'3'} = $window3;
		$vars->{'4'} = $window4;

		# get totals
		$vars->{'total_opened'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'NEW','ASSIGNED','REOPENED'");
		$vars->{'total_resolved'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'RESOLVED','VERIFIED'");
		$vars->{'total_closed'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'CLOSED'");

		print $cgi->header();
	    $template->process("browse/browse-classification.html.tmpl", $vars)
		        	|| ThrowTemplateError($template->error());
	    exit;

	}
}

#
# action='browse_window'
#
elsif ($action eq 'browse_window') {

	my $window_id = trim($cgi->param('window') || '');
	my $window;

	if ($cgi->param('product')) { # browse for product

		# TODO - add a check if user is allowed to see the product
		my $product = new Bugzilla::Product({name => $cgi->param('product')});
        $vars->{'product_url'} = $product->milestone_url;
		$vars->{'product_desc'} = $product->description;


		@browse_list = Bugzilla::Browse::GetBrowseDef(1);
		$vars->{'browse_list'} = \@browse_list;

		# build the result for each window
		$window  = Bugzilla::Browse::GetFieldQueryResultsForProduct($product->id,$browse_list[$window_id-1] {'bugs_field_name'}, $browse_list[$window_id-1] {'table_name'}, $browse_list[$window_id-1] {'field_name'}, $browse_list[$window_id-1] {'key_field_name'});

		$vars->{'title'} = "Browse ".Bugzilla->params->{"product_field_name"}." by ".$browse_list[$window_id-1] {'browse_by'};
		$vars->{'browse_by'} = $browse_list[$window_id-1] {'browse_by'};
		$vars->{'search_field_name'} = $browse_list[$window_id-1] {'search_field_name'};
		$vars->{'window'} = $window;

		# get totals
		$vars->{'total_opened'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'NEW','ASSIGNED','REOPENED'");
		$vars->{'total_resolved'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'RESOLVED','VERIFIED'");
		$vars->{'total_closed'} = Bugzilla::Browse::GetTotalForProduct($product->id,"'CLOSED'");

		print $cgi->header();
       	$template->process("browse/browse-product.html.tmpl", $vars)
	     					|| ThrowTemplateError($template->error());
       	exit;

	} else {  # browse for classification

		@browse_list = Bugzilla::Browse::GetBrowseDef(2);
		$vars->{'browse_list'} = \@browse_list;

		# get the list of the products ids
		my $classification = new Bugzilla::Classification({'name' => $classification_name});

 		my $products_list = "";
 		my $products = $classification->products;
		foreach my $p (@$products) {
			$products_list .= $p->id.",";
		}
		if ($products_list ne "") {
			chop $products_list;
		}

		# build the result for each window
		$window  = Bugzilla::Browse::GetFieldQueryResultsForClassification($classification->id,$products_list,$browse_list[$window_id-1] {'bugs_field_name'}, $browse_list[$window_id-1] {'table_name'}, $browse_list[$window_id-1] {'field_name'}, $browse_list[$window_id-1] {'key_field_name'});

		$vars->{'title'} = "Browse Classification by  ".$browse_list[$window_id-1] {'browse_by'};
		$vars->{'browse_by'} = $browse_list[$window_id-1] {'browse_by'};
		$vars->{'search_field_name'} = $browse_list[$window_id-1] {'search_field_name'};
		$vars->{'window'} = $window;

		# get totals
		$vars->{'total_opened'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'NEW','ASSIGNED','REOPENED'");
		$vars->{'total_resolved'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'RESOLVED','VERIFIED'");
		$vars->{'total_closed'} = Bugzilla::Browse::GetTotalForClassification($products_list,"'CLOSED'");

 		print $cgi->header();
     	$template->process("browse/browse-classification.html.tmpl", $vars)
	      					|| ThrowTemplateError($template->error());
       	exit;

	}
}

#
# action='option' -> present the form to define browse option
#
elsif ($action eq 'option') {
#TODO
exit;
}

else {
	exit;
}
