/*
    Defines the default styles available in the CKEditor used for the
    submission of journal articles. These styles should be in sync with
    the CSS styles and the HTML templates of the journal

    See config.stylesSet in the configuration file.
*/

CKEDITOR.stylesSet.add( 'journal-editor-style',
[

    // Inline styles
    { name : 'Article Header', element : 'p', attributes : { 'class' : 'articleHeader' } },
    { name : 'Caption', element : 'span', styles : { 'class' : 'articleHeader' } },
    { name : 'Computer Code', element : 'code' },
    { name : 'Keyboard Phrase', element : 'kbd' },
    { name : 'Sample Text', element : 'samp' },
    { name : 'Variable', element : 'var' },
    { name : 'Deleted Text', element : 'del' },
    { name : 'Inserted Text', element : 'ins' },
    { name : 'Cited Work', element : 'cite' },
    { name : 'Inline Quotation', element : 'q' },

    // Object styles
    { name : 'Image on Left', element : 'img', attributes : { 'class' : 'phl' } },
    { name : 'Image on Right', element : 'img', attributes : { 'class' :  'phr'} },
    { name : 'Centered Image', element : 'img', attributes : { 'class' :  'ph'} },
    { name : 'Image With Caption on Left', element : 'table', attributes : { 'class' :  'phl'} },
    { name : 'Image With Caption on Right', element : 'table', attributes : { 'class' :  'phr'} },
    { name : 'Centered Image With Caption', element : 'table', attributes : { 'class' :  'ph'} }
]);
