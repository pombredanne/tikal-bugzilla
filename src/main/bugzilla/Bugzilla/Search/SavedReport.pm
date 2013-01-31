# -*- Mode: perl; indent-tabs-mode: nil -*-
#


use strict;

package Bugzilla::Search::SavedReport;

use base qw(Bugzilla::Object);

use Bugzilla::CGI;
use Bugzilla::Constants;
use Bugzilla::Group;
use Bugzilla::Error;
use Bugzilla::User;
use Bugzilla::Util;

#############
# Constants #
#############

use constant DB_TABLE => 'namedreports';

use constant DB_COLUMNS => qw(
    id
    userid
    name
    report
);

use constant REQUIRED_CREATE_FIELDS => qw(name report);

use constant VALIDATORS => {
    name       => \&_check_name,
    report      => \&_check_report,
    link_in_footer => \&_check_link_in_footer,
};

use constant UPDATE_COLUMNS => qw(name report);

##############
# Validators #
##############

sub _check_link_in_footer { return $_[1] ? 1 : 0; }

sub _check_name {
    my ($invocant, $name) = @_;
    $name = trim($name);
    $name || ThrowUserError("report_name_missing");
    $name !~ /[<>&]/ || ThrowUserError("illegal_report_name");
    if (length($name) > MAX_LEN_QUERY_NAME) {
        ThrowUserError("report_name_too_long");
    }
    return $name;
}

sub _check_report {
    my ($invocant, $report) = @_;
    $report || ThrowUserError("buglist_parameters_required");
    my $cgi = new Bugzilla::CGI($report);
    $cgi->clean_search_url;
    return $cgi->query_string;
}

#########################
# Database Manipulation #
#########################

sub create {
    my $class = shift;
    Bugzilla->login(LOGIN_REQUIRED);
    my $dbh = Bugzilla->dbh;
    $class->check_required_create_fields(@_);
    $dbh->bz_start_transaction();
    my $params = $class->run_create_validators(@_);

    # Right now you can only create a Saved Report for the current user.
    $params->{userid} = Bugzilla->user->id;

    my $lif = delete $params->{link_in_footer};
    my $obj = $class->insert_create_data($params);
    if ($lif) {
        $dbh->do('INSERT INTO namedreports_link_in_footer 
                  (user_id, namedreport_id) VALUES (?,?)',
                 undef, $params->{userid}, $obj->id);
    }
    $dbh->bz_commit_transaction();

    return $obj;
}

#####################
# Complex Accessors #
#####################

sub edit_link {
    my ($self) = @_;
    return $self->{edit_link} if defined $self->{edit_link};
    my $cgi = new Bugzilla::CGI($self->url);
    $self->{edit_link} = $cgi->canonicalise_query;
    return $self->{edit_link};
}

sub link_in_footer {
    my ($self, $user) = @_;
    # We only cache link_in_footer for the current Bugzilla->user.
    return $self->{link_in_footer} if exists $self->{link_in_footer} && !$user;
    my $user_id = $user ? $user->id : Bugzilla->user->id;
    my $link_in_footer = Bugzilla->dbh->selectrow_array(
        'SELECT 1 FROM namedreports_link_in_footer
          WHERE namedreport_id = ? AND user_id = ?', 
        undef, $self->id, $user_id) || 0;
    $self->{link_in_footer} = $link_in_footer if !$user;
    return $link_in_footer;
}

sub shared_with_group {
    my ($self) = @_;
    return $self->{shared_with_group} if exists $self->{shared_with_group};
    # Bugzilla only currently supports sharing with one group, even
    # though the database backend allows for an infinite number.
    my ($group_id) = Bugzilla->dbh->selectrow_array(
        'SELECT group_id FROM namedreport_group_map WHERE namedreport_id = ?',
        undef, $self->id);
    $self->{shared_with_group} = $group_id ? new Bugzilla::Group($group_id) 
                                 : undef;
    return $self->{shared_with_group};
}

sub shared_with_users {
    my $self = shift;
    my $dbh = Bugzilla->dbh;

    if (!exists $self->{shared_with_users}) {
        $self->{shared_with_users} =
          $dbh->selectrow_array('SELECT COUNT(*)
                                   FROM namedreports_link_in_footer
                             INNER JOIN namedreports
                                     ON namedreport_id = id
                                  WHERE namedreport_id = ?
                                    AND user_id != userid',
                                  undef, $self->id);
    }
    return $self->{shared_with_users};
}

####################
# Simple Accessors #
####################

sub url          { return $_[0]->{'report'}; }

sub user {
    my ($self) = @_;
    return $self->{user} if defined $self->{user};
    $self->{user} = new Bugzilla::User($self->{userid});
    return $self->{user};
}

############
# Mutators #
############

sub set_name       { $_[0]->set('name',       $_[1]); }
sub set_url        { $_[0]->set('report',      $_[1]); }

1;

__END__

=head1 NAME

Bugzilla::Search::SavedReport - A saved report

=head1 SYNOPSIS

 use Bugzilla::Search::SavedReport;

 my $report = new Bugzilla::Search::SavedReport($report_id);

 my $edit_link  = $report->edit_link;
 my $search_url = $report->url;
 my $owner      = $report->user;
 my $num_subscribers = $report->shared_with_users;

=head1 DESCRIPTION

This module exists to represent a bugzilla report that has been
saved to the database.

This is an implementation of L<Bugzilla::Object>, and so has all the
same methods available as L<Bugzilla::Object>, in addition to what is
documented below.

=head1 METHODS

=head2 Constructors and Database Manipulation

=over

=item C<new>

Does not accept a bare C<name> argument. Instead, accepts only an id.

See also: L<Bugzilla::Object/new>.

=back


=head2 Accessors

These return data about the object, without modifying the object.

=over

=item C<edit_link>

A url with which you can edit the search.

=item C<url>

The CGI parameters for the search, as a string.

=item C<link_in_footer>

Whether or not this search should be displayed in the footer for the
I<current user> (not the owner of the search, but the person actually
using Bugzilla right now).

=item C<shared_with_group>

The L<Bugzilla::Group> that this search is shared with. C<undef> if
this search isn't shared.

=item C<shared_with_users>

Returns how many users (besides the author of the saved report) are
using the saved report, i.e. have it displayed in their footer.

=back
