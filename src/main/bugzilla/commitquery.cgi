#!/usr/bin/perl -wT
# -*- Mode: perl; indent-tabs-mode: nil -*-


use strict;
use lib qw(. lib);

use Bugzilla;
use Bugzilla::Util;

my $dbh = Bugzilla->dbh;
my $cgi = Bugzilla->cgi;

my $bug_id = $cgi->param('id') || "";
trick_taint($bug_id);

my $ans = $dbh->selectcol_arrayref("SELECT 'true' FROM bugs WHERE bug_id=$bug_id AND bug_status IN ('NEW','ASSIGNED','REOPENED')");

print "Content-type: text/html\n\n";
print $ans->[0];
