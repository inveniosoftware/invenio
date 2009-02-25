/*Define here the config of the FCKEditor used in CDS Invenio.

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
['Bold','Italic','Underline','StrikeThrough','-','Subscript','Superscript', '-','TextColor'],
['OrderedList','UnorderedList','-','Outdent','Indent','Blockquote'],
['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],
['Link','Unlink'],
['Image','Table','Rule','Smiley','SpecialChar']
] ;


FCKConfig.EditorAreaCSS = '/img/cds.css'

/* Though not recommended, it is much better that users gets a
   <br/> when pressing carriage return than a <p> element. Then
   when a user replies to a webcomment without the FCKeditor,
   line breaks are nicely displayed.
*/
FCKConfig.EnterMode = 'br'