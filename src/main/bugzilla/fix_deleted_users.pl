#!/usr/bin/perl -w
# -*- Mode: perl; indent-tabs-mode: nil -*-
#

use strict;
use lib qw(. lib);

use Bugzilla;
my $dbh = Bugzilla->dbh;

my $userid = $ARGV[0];

print "Fixing deleted users to userid $userid \n";

$dbh->do("update bugs set assigned_to=$userid where assigned_to not in (select userid from profiles)");

$dbh->do("update bugs set reporter=$userid where reporter not in (select userid from profiles)");

$dbh->do("update bugs set resolver=$userid where resolver not in (select userid from profiles)");

$dbh->do("update bugs set qa_contact=$userid where qa_contact not in (select userid from profiles)");

$dbh->do("update bugs_activity set who=$userid where who not in (select userid from profiles)");

$dbh->do("update attachments set submitter_id=$userid where submitter_id not in (select userid from profiles)");

$dbh->do("update longdescs set who=$userid where who not in (select userid from profiles)");

$dbh->do("delete from cc where who not in (select userid from profiles)");