
..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Previewing files
================
Invenio has support for previewing many of the most popular file formats
including PDF, ZIP, Markdown, images and Jupyter Notebooks. In this section we
will discuss how previewing files work in Invenio and which options are
available.

`Invenio-Previewer <https://invenio-previewer.readthedocs.io/en/latest/>`_
allows you to register previewers based on the file extension. To preview
files, ensure that a preview endpoint have been configured in your
``config.py``, like this:

.. code:: python

    RECORDS_UI_ENDPOINTS=dict(
        recid_previewer=dict(
            pid_type='recid',
            route='/records/<pid_value>/preview/<filename>',
            view_imp='invenio_previewer.views:preview',
            record_class='invenio_records_files.api:Record',
        ),
    )

Upload a file (see :ref:`managing-files`) of a type supported by the previewer,
e.g. ``myfile.md``, and visit ``/records/<pid_value>/preview/myfile.md`` to see
your file rendered in the browser.

The available previewers can be configured in the ``PREVIEWER_PREFERENCE``
variable in ``config.py`` which is a list of previewers. The order in which
they appear in the list will be the order they are used when finding a suitable
previewer.

Invenio-Previewer supports previewing images out-of-the-box however it's very
basic. If you need more advanced image support, like thumbnails, please see
:ref:`preview-with-iiif`.

For a full example of how to use Invenio-Previewer, please see the
`usage <https://invenio-previewer.readthedocs.io/en/latest/usage.html>`_ guide.

.. _preview-with-iiif:

Preview images using IIIF
-------------------------
Invenio-IIIF implements the `IIIF API <https://iiif.io/>`_ which is a standard
for describing and delivering images over the web. `Invenio-IIIF <https://invenio-iiif.readthedocs.io/en/latest/>`_
allows you to generate thumbnails, resize and zoom images as well as previewing
images using Invenio-Previewer.

To activate the IIIF image previewer you need to add ``iiif_image`` to the list
of supported previewers in ``PREVIEWER_PREFERENCE``, e.g.:

.. code:: python

    PREVIEWER_PREFERENCE = [
        'iiif_image',
        'json_prismjs',
        'xml_prismjs',
        'pdfjs',
        'zip',
    ]

The IIIF API is available by default on ``/api/iiif`` and to generate
valid image URLs, the utilify function `invenio_iiif.utils.ui_iiif_image_url <https://invenio-iiif.readthedocs.io/en/latest/api.html#invenio_iiif.utils.ui_iiif_image_url>`_
can be used. Given that you have an image object ``img_obj`` belonging to a bucket
``bucket`` (see :ref:`managing-files`), an image URL can be generated for that
image as in the example below:

.. code:: python

    from invenio_iiif.utils import ui_iiif_image_url
    image_url = ui_iiif_image_url(
          obj=img_obj, version='v2', region='full', size='full', rotation=0,
          quality='default', image_format='png')

The generated image URL will look similar to this:

``/iiif/<bucket_id>:<version_id>:img.png/full/full/0/default.png``

For a more complete guide and more detailed documentation about Invenio-IIIF,
see the `usage guide <https://invenio-iiif.readthedocs.io/en/latest/usage.html>`_.

Custom previewer
----------------
Invenio-Previewer has an extensible API for creating new previewers so if
you need to preview a file type not supported you can create your own
custom previewer. Please see the section about `developing your own previewer <https://invenio-previewer.readthedocs.io/en/latest/usage.html#custom-previewer>`_
for Invenio-Previewer.
