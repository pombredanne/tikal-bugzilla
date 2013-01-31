# -*- Mode: perl; indent-tabs-mode: nil -*-
#


use strict;

package Bugzilla::Menu;

use Bugzilla::Error;

###############################
####    Initialization     ####
###############################

sub _init {
    my $self = shift;
    return $self;
}

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

###############################
####      Subroutines      ####
###############################

sub PopulateClassificationAndProducts {

	my $dbh = Bugzilla->dbh;
	my $vars;
	
	# If the user cannot enter bugs in any product, stop here.
    my @enterable_products = @{Bugzilla->user->get_enterable_products};
    #ThrowUserError('no_products') unless scalar(@enterable_products);

    my @classifications;

    if (Bugzilla->params->{'useclassification'}) {
    	my $class;
        # Get all classifications with at least one enterable product.
        foreach my $product (@enterable_products) {
            $class->{$product->classification_id}->{'object'} ||=
                new Bugzilla::Classification($product->classification_id);
            # Nice way to group products per classification, without querying
            # the DB again.
            push(@{$class->{$product->classification_id}->{'products'}}, $product);
        }
        @classifications = sort {$a->{'object'}->sortkey <=> $b->{'object'}->sortkey
                                 || lc($a->{'object'}->name) cmp lc($b->{'object'}->name)}
                                (values %$class);
        $vars->{'products_menu'} = [map {$_->{'object'}} @classifications];
    } else {
        $vars->{'products_menu'} = \@enterable_products;
    }

	return $vars;

}

1;