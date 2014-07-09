/*Define here the config of the CKEditor used in Invenio.

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

config.toolbar_WebComment = [
			     ['Preview'],
			     ['PasteText','PasteFromWord'],
			     ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
			     '/',
			     ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
			     ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],
			     ['Link','Unlink'],
                             ['HorizontalRule','Smiley','SpecialChar','ScientificChar']
			     ];

config.skin = 'v2';
config.resize_dir = 'vertical';

/* Enable browser built-in spellchecker */
config.disableNativeSpellChecker = false;
config.browserContextMenuOnCtrl = true;

/* Remove "status" bar at the bottom of the editor displaying the DOM path*/
config.removePlugins = 'elementspath';

/* Some styling that will only apply inside the CKeditor, including to
   simulate the the ".commentbox" CSS class in WebComment case. */
config.contentsCss = ['/css/invenio.css', '/css/ckeditor/invenio-ckeditor-content.css'];

/* Though not recommended, it is much better that users gets a
   <br/> when pressing carriage return than a <p> element. Then
   when a user replies to a webcomment without the CKeditor,
   line breaks are nicely displayed.
*/
config.enterMode = CKEDITOR.ENTER_BR;

/* Load our Scientific Characters panel */
config.extraPlugins = 'scientificchar';
}
