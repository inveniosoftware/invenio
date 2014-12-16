/*
    Custom configuration for the "Templates" menu of the FCKeditor used in
    journal submission pages:
    - full journal sample page
    - image with caption layouts

   See config.templates_files in the configuration file.
*/

CKEDITOR.addTemplates( 'default',
{
	// The name of the subfolder that contains the preview images of the templates.
	imagesPath : '/img/' ,

	// Template definitions.
	templates :
		[
			{
				title: 'Sample Journal Page',
				image: 'journal-template1.gif',
				description: 'A full journal page with title, content and images.',
				html:
                                        '<p class="articleHeader">Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum</p>' +
                               '<p><div class="phlwithcaption"><div class="imageScale"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2007/0712017/0712017_01/0712017_01-A5-at-72-dpi.jpg"/></div><p>Maecenas erat felis, posuere placerat, dignissim ut, vehicula in, orci.</p></div>Vestibulum mollis velit vitae arcu. Curabitur nunc nisl, sollicitudin ac, tincidunt eget, fringilla nec, velit. Proin facilisis libero at risus. Nam suscipit elit vitae tortor. Proin hendrerit quam id ligula. Curabitur fringilla. Morbi dapibus. Suspendisse a libero nec metus scelerisque suscipit. Praesent nulla diam, pharetra at, consequat a, pellentesque at, lacus. Nullam hendrerit ultricies leo. </p>' +
                                '<p>Nulla eros. Proin dapibus leo in risus. Suspendisse potenti. Nam ut justo. Nulla sodales eros ac massa. Curabitur facilisis neque at lectus. Quisque non nunc non sapien elementum sagittis. Morbi iaculis tempor arcu. In porttitor, augue ut viverra adipiscing, massa mi ullamcorper orci, et tempus ligula nisi et risus. Proin turpis quam, tincidunt at, malesuada ac, aliquam id, nunc. In nec libero vitae nibh ornare vestibulum. Nunc luctus, ligula eu porttitor eleifend, elit nibh venenatis metus, cursus congue tortor risus a libero. Maecenas vitae mi at neque posuere laoreet.</p>' +
                                 '<p><div class="phrwithcaption"><div class="imageScale"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2008/0806011/0806011_04/0806011_04-A5-at-72-dpi.jpg"/></div><p>Curabitur neque nibh, venenatis in, imperdiet in, hendrerit id, massa.</p></div>Nam diam. Praesent nec massa a elit porttitor rhoncus. Fusce convallis auctor arcu. Fusce commodo mauris sed neque. Pellentesque adipiscing. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Quisque luctus erat eget lorem. Quisque ac nunc. Aliquam pellentesque, purus sed aliquam volutpat, risus turpis aliquam augue, vel tristique mi lacus non leo. Etiam rutrum molestie sapien. Phasellus cursus, quam id placerat porta, lectus nisi aliquet nisl, at varius nibh felis vitae lacus. Proin semper posuere pede. Praesent fringilla libero sit amet lectus. Nam lectus mauris, vestibulum in, fringilla et, fringilla vel, quam. Maecenas ultricies cursus metus.</p>'
			},
			{
				title: 'Wide Centered Image With Caption',
				image: 'journal-template5.gif',
				description: 'Full-width centered block for an image and its caption.',
				html:
					'<div class="phwidewithcaption"><div class="imageScaleWide"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2008/0801015/0801015_01/0801015_01-A5-at-72-dpi.jpg"/></div><p>Pellentesque sapien mi, pharetra vitae, auctor eu, congue sed, turpis.</p></div>'
			},

			{
				title: 'Left Image With Caption',
				image: 'journal-template2.gif',
				description: 'Left-aligned block for an image and its caption.',
				html:
					'<div class="phlwithcaption"><div class="imageScale"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2007/0712010/0712010_03/0712010_03-A5-at-72-dpi.jpg"/></div><p>Morbi purus sem, hendrerit vitae, viverra vitae, faucibus at, quam.</p></div>'
			},
			{
				title: 'Centered Image With Caption',
				image: 'journal-template3.gif',
				description: 'Centered block for an image and its caption.',
				html:
					'<div class="phwithcaption"><div class="imageScale"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2008/0801015/0801015_01/0801015_01-A5-at-72-dpi.jpg"/></div><p>Pellentesque sapien mi, pharetra vitae, auctor eu, congue sed, turpis.</p></div>'
			},
			{
				title: 'Right Image With Caption',
				image: 'journal-template4.gif',
				description: 'Right-aligned single block for an image and its caption.',
				html:
					'<div class="phrwithcaption"><div class="imageScale"><img src="http://mediaarchive.cern.ch/MediaArchive/Photo/Public/2007/0711016/0711016_03/0711016_03-A5-at-72-dpi.jpg"/></div><p>Aenean mattis justo eu diam varius convallis.</p></div>'
			}
		]
});
