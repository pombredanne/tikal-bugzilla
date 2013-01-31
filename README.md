Tikal Bugzilla
==============

Tikal Bugzilla is a customization of Mozilla Bugzilla based on the latest community 3.4 version.
Tikal Bugzilla has most of community Bugzilla latest features with addition of many new features as well as a whole new 'application like' GUI that enables intuitive and easy to use Bugzilla.

---------------------------

New issues can be opened for Tikal Bugzilla at http://dev.tikalk.com/bugzilla/enter_bug.cgi?product=tikal-alm for component 'bugzilla34'

---------------------------
Bugzilla enhancements list:
---------------------------

1. 'Application like' GUI :
	- New look
	- Dynamic menus
	- Edit Issue page redesign with actions bars
	- Add required fields indication (*)  on Create and Edit issue pages

2. Customizable Bugzilla Homepage that can presents:
	- Products statistics per Target milestone/ version
	- The list of new and open issues for  the logged user
	- User saved queries results

3. An Issue Type feature, for using Bugzilla as an Issue Tracker to track task, bugs, features and etc.
	
4. Default issue type can be defined on system and product levels.
	
5. One level Subtasks functionality - this option helps to split an issue to a number of smaller tasks that can be assigned to different components and users, thus providing a better picture of the progress on the issue. 
	This new feature also allows each party that needs to be involved in resolving the issue to better understand what part of the process they are responsible for. 
	Good example for use of this functionality is the Feature Management.
	Additional features enabled by inclusion of Subtasks:
	- Issue of any issue type in Bugzilla can have subtasks (defined per issue type).
	- Issue of any issue type in Bugzilla can be a subtask (defined per issue type).
	- 'Template' list of subtasks can be defined for an issue type; additional subtasks can be added in this case as well.
	- Validation of issue's subtasks on 'Resolve' can be 'turned on' for an issue type – means that user can not change its status to 'Resolved' as long as there are open subtasks for this issue.
	- Subtask can be detached from its “parent”
	- “Common fields” validation can be performed
	
6. Browse Product & Classification page - shows information related to product or classification, counts per components, per severity etc.

7. Enhancements to Bugzilla original Custom Fields feature:
	- Add 5 types of mandatory indicators:
		always
		for new issue only
		for existing issue only
		for resolved fixed issue only
		for reopened issues only
	- Add Issue Type field to the visibility options 
	- Add default values for custom fields
	- Add “system” custom fields:
		implemented as custom fields
		not displayed in default templates (create and edit issue pages) – should be added in custom templates only
	- Add “system table” custom fields:
		can get data from existing table instead of default (single and multi select fields)
		supports only Version table at the moment – used for 'Target Version', 'Fixed In fields'
	- Add custom fields to the Search 
	- Add multi-valued custom fields to the Search results
	- Add visibility fields columns to the valid values list pages
	- Display the value of the control field that make the custom field value visible in the Field Values page
	- Add 'inactive' option for custom fields values – a possibility to make a value “invisible” for new issues, but keep the history issues with correct values
	
8. Templates by Product & Issue Type mechanism for Create/Edit Issues pages
	There are cases when issues for different products and/or issue types should have a different layout and/or different validations, 
	and this feature gives a possibility to easily add a new layout which will be picked u automatically by Bugzilla. 
	For example, if you want to have a different layout for Task issue type, all you need is to create templates named create-Task.html.tmpl (for Create Issue page) and edit-Task.html.tmpl (for Edit Issue page) and put them in correct folders. 
	If your issue type is 'Task', Bugzilla will load it with this template. 
	Same for the product Product1 - create-Product1.html.tmpl (for Create Issue page) and edit-Product1.html.tmpl (for Edit Issue page). 
	You can also create a template for combination of the product and issue type, for example: create-Product1-Bug.html.tmpl
	
9. Enhancements to the Version field:
	- Added status to the Version field: UNRELEASED, RELEASED, FINAL and ARCHIVED 
	- Version field will show only RELEASED and FINAL versions in the drop-down list of Version on New and Edit Issue pages
	- ARCHIVED versions will not be displayed on the New & Edit Issue pages
	- Custom version fields (like Target Version & Fixed In) can be added as 'system_table' custom fields, using versions list of UNRELEASED and RELEASED versions.
	- Added sortkey for Versions
	
10. A "View SCM Activity" link, that enables to see all bug related version control activity. Support for multiple viewvc roots (per product)

11. CRM Connectivity feature enables to relate bugs to specific CRM Id's (customer ticketing).

12. 'do not send mail' flag to the "Edit Issue" and 'Add Attachment” pages – very useful for minor changes performed on an issue.

13. 'Auto-Reassign' feature:
	- automatically re-assign to the reporter when status changed to RESOLVED
	- automatically re-assign to the previous assignee (Resolver) when status changed to REOPENED
	- 'Resolver' read-only field is set to the logged user that resolves the issue and appears in the Edit Issue screen
	NOTE: If 'auto-reassign' is turned-on, 'Resolver' will be set according to auto-reassign feature and not to the actual resolving user.
	
14. Added an option to make old Components and Milestones “invisible” for new issues, but keep the history issues with correct values.

15. Added query fields for whining event that will appear in the mails.
	NOTE: if no fields are chosen, no whining mail will be sent.

16. Template for new issue description (in parameters)

17. Saved reports (like saved searches)

18. Commit check query – can be called from a pre-commit check from version control to verify that bug_id exists and etc.

19. Parameter for Summary field length

20. Indicators to use : URL, dependency feature

21. HTML tags for fields: URL, Product, Component, QA Contact

22. 'SendMail' link on the Edit Issue page - opens an email to the issue assignee with all issue details

23. Added client side validation checks on Create/Edit Issue and Add Attachment pages

24. Added utilities function that can be called through URL to use by scripts or integration with other tools