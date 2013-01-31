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
# The Initial Developer of the Original Code is Netscape Communications
# Corporation. Portions created by Netscape are
# Copyright (C) 1998 Netscape Communications Corporation. All
# Rights Reserved.
#
# Contributor(s): Terry Weissman <terry@mozilla.org>
#                 Dawn Endico <endico@mozilla.org>
#                 Dan Mosedale <dmose@mozilla.org>
#                 Joe Robins <jmrobins@tgix.com>
#                 Jacob Steenhagen <jake@bugzilla.org>
#                 J. Paul Reed <preed@sigkill.com>
#                 Bradley Baetz <bbaetz@student.usyd.edu.au>
#                 Joseph Heenan <joseph@heenan.me.uk>
#                 Erik Stambaugh <erik@dasbistro.com>
#                 Frédéric Buclin <LpSolit@gmail.com>
#

package Bugzilla::Config::BugFields;

use strict;

use Bugzilla::Config::Common;
use Bugzilla::Field;

$Bugzilla::Config::BugFields::sortkey = "04";

sub get_param_list {
  my $class = shift;

  my @legal_priorities = @{get_legal_field_values('priority')};
  my @legal_severities = @{get_legal_field_values('bug_severity')};
  my @legal_platforms  = @{get_legal_field_values('rep_platform')};
  my @legal_OS         = @{get_legal_field_values('op_sys')};

  my @param_list = (
  {
   name => 'useclassification',
   type => 'b',
   default => 0
  },

  {
   name => 'usetargetmilestone',
   type => 'b',
   default => 0
  },

  {
   name => 'useqacontact',
   type => 'b',
   default => 0
  },

  {
   name => 'usestatuswhiteboard',
   type => 'b',
   default => 0
  },

  {
   name => 'usevotes',
   type => 'b',
   default => 0
  },

  {
   name => 'usebugaliases',
   type => 'b',
   default => 0
  },

  {
   name => 'use_see_also',
   type => 'b',
   default => 1
  },

  {
   name => 'defaultpriority',
   type => 's',
   choices => \@legal_priorities,
   default => $legal_priorities[-1],
   checker => \&check_priority
  },

  {
   name => 'defaultseverity',
   type => 's',
   choices => \@legal_severities,
   default => $legal_severities[-1],
   checker => \&check_severity
  },

  {
   name => 'defaultplatform',
   type => 's',
   choices => ['', @legal_platforms],
   default => '',
   checker => \&check_platform
  },

  {
   name => 'defaultopsys',
   type => 's',
   choices => ['', @legal_OS],
   default => '',
   checker => \&check_opsys
  },
  
  {
   name    => 'opsys_field_name',
   type    => 't',
   default => 'OS',
  },
  
  {
   name    => 'url_field_name',
   type    => 't',
   default => 'URL',
  },

  {
   name    => 'use_url',
   type    => 'b',
   default => 0,
  },

  {
   name    => 'use_issue_dependency',
   type    => 'b',
   default => 1,
  },
  
  {
   name => 'use_send_email_link',
   type => 'b',
   default => 0
  },

  {
   name    => 'product_field_name',
   type    => 't',
   default => 'Product'
  },
  
  {
   name    => 'component_field_name',
   type    => 't',
   default => 'Component'
  },

  {
   name    => 'qa_contact_field_name',
   type    => 't',
   default => 'QA Contact',
  },
  
  {
   name    => 'use_crm_id',
   type    => 'b',
   default => 1,
  },
  
  {
   name    => 'crm_base_url',
   type    => 't',
   default => 'http://you-havent-visited-editparams.cgi-yet/',

  },
  
  {
   name    => 'crm_id_field_name',
   type    => 't',
   default => 'CRM Id',
  },
  
  {
   name    => 'summary_field_length',
   type    => 't',
   default => '80',
  },
  
  {
   name => 'show_desc_with_summary',
   type => 'b',
   default => 0
  },
  
   {
   name => 'newissuedesc_template',
   type => 'l',
   default => 'DESCRIPTION:

EXPECTED:

ACTUAL:

'
},

{
   name    => 'use_last_changed_fields',
   type    => 'b',
   default => 0
  },
  
  {
	name => 'hebrew_text',
	type => 'b',
	default => 0
  } );
  return @param_list;
}

1;
