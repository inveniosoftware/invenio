/*Define here the config of the CKEditor used in Invenio for
  journal articles submission.

  Users/admin:
  Since the editor is used in various contexts that require different
  settings, most variables are set up directly in the module that
  calls the editor: variables that you might define here will be
  overriden, excepted notably the toolbar sets.

  Developers:
  Here is the best/only place to define custom toolbar sets.
 */
CKEDITOR.editorConfig = function( config )
{
config.toolbar_WebJournal = [
['Source', 'Preview'],
['Templates', '-','PasteText','PasteFromWord'],
['Undo','Redo','-','Find','Replace','-','RemoveFormat'],
['Link','Unlink'],
['Image','Table','HorizontalRule','SpecialChar'],
'/',
['Bold','Italic','Underline','Strike','-','Subscript','Superscript', '-','TextColor'],
['NumberedList','BulletedList','-','Outdent','Indent','Blockquote','CreateDiv'],
['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
'/',
['Styles','Format', 'FontSize'],
['Maximize','ShowBlocks']
];

config.skin = 'v2';
config.resize_enabled = false;

/* Remove "status" bar at the bottom of the editor displaying the DOM path*/
config.removePlugins = 'elementspath';

config.contentsCss = '/css/AtlantisTimes.css' ;
config.bodyClass = 'ckeditor_body';
config.stylesSet = 'journal-editor-style:/ckeditor/journal-editor-styles.js';
config.templates_files = [ '/ckeditor/journal-editor-templates.js' ];
config.enterMode = CKEDITOR.ENTER_P;
/* Tags that are removed when clicking on "Remove format" button:
   we need to add 'p' here
*/
config.removeFormatTags = 'b,big,code,del,dfn,em,font,i,ins,kbd,q,samp,small,span,strike,strong,sub,sup,tt,u,var,p' ;
config.templates_replaceContent = false;
}
