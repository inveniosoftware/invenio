/*Define here the config of the FCKEditor used in Invenio for
  journal articles submission.

  Users/admin:
  Since the editor is used in various contexts that require different
  settings, most variables are set up directly in the module that
  calls the editor: variables that you might define here will be
  overriden, excepted notably the toolbar sets.

  Developers:
  Here is the best/only place to define custom toolbar sets.
 */

FCKConfig.ToolbarSets["WebJournal"] = [
['Source', 'Preview'],
['Templates', '-','PasteText','PasteWord'],
['Undo','Redo','-','Find','Replace','-','RemoveFormat'],
['Link','Unlink'],
['Image','Table','Rule','SpecialChar'],
'/',
['Bold','Italic','Underline','StrikeThrough','-','Subscript','Superscript', '-','TextColor'],
['OrderedList','UnorderedList','-','Outdent','Indent','Blockquote','CreateDiv'],
['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],
'/',
['Style','FontFormat'],
['FontSize'],
['FitWindow','ShowBlocks']
];

FCKConfig.EditorAreaCSS = '/img/AtlantisTimes.css' ;
FCKConfig.CustomStyles = {};
FCKConfig.EditorAreaStyles = 'body { background-color: White !important}';
FCKConfig.StylesXmlPath = '/fckeditor/journal-editor-styles.xml' ;
FCKConfig.TemplatesXmlPath = '/fckeditor/journal-editor-templates.xml' ;
FCKConfig.EnterMode = 'p';
/* Tags that are removed when clicking on "Remove format" button:
   we need to add 'p' here
*/
FCKConfig.RemoveFormatTags = 'b,big,code,del,dfn,em,font,i,ins,kbd,q,samp,small,span,strike,strong,sub,sup,tt,u,var,p' ;
FCKConfig.TemplateReplaceAll = false ;
