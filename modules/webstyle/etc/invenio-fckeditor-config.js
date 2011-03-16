/*Define here the config of the FCKEditor used in Invenio.

  Users/admin:
  Since the editor is used in various contexts that require different
  settings, most variables are set up directly in the module that
  calls the editor: variables that you might define here will be
  overriden, excepted notably the toolbar sets.

  Developers:
  Here is the best/only place to define custom toolbar sets.
 */

FCKConfig.ToolbarSets["WebComment"] = [
['Preview'],
['PasteText','PasteWord'],
['Undo','Redo','-','RemoveFormat'],
'/',
['Bold','Italic','Underline','StrikeThrough','-','Subscript','Superscript'],
['OrderedList','UnorderedList','-','Outdent','Indent','Blockquote'],
['Link','Unlink'],
['SpecialChar']
] ;


FCKConfig.EditorAreaCSS = '/img/invenio.css'

/* Some styling that will only apply inside the FKCeditor, to simulate
   the the ".commentbox" CSS class in WebComment case. */
FCKConfig.EditorAreaStyles = 'blockquote {margin:0;padding:0;display:inline;} blockquote div {padding: 0 10px 0px 10px;border-left: 2px solid #36c;margin-left: 10px;display:inline;}';


/* Though not recommended, it is much better that users gets a
   <br/> when pressing carriage return than a <p> element. Then
   when a user replies to a webcomment without the FCKeditor,
   line breaks are nicely displayed.
*/
FCKConfig.EnterMode = 'br'
