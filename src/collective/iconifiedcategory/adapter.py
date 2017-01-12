# -*- coding: utf-8 -*-
"""
collective.iconifiedcategory
----------------------------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from Acquisition import aq_base
from zope.annotation import IAnnotations
from plone import api
from plone.app.contenttypes.interfaces import IFile
from plone.app.contenttypes.interfaces import IImage
from plone.app.contenttypes.interfaces import ILink

import logging
logger = logging.getLogger('collective.iconifiedcategory')

from collective.documentviewer.settings import GlobalSettings
from collective.documentviewer.settings import Settings
from collective.documentviewer.utils import allowedDocumentType
from collective.iconifiedcategory import utils
from collective.iconifiedcategory.interfaces import IIconifiedPreview
from collective.iconifiedcategory.content.subcategory import ISubcategory


class CategorizedObjectInfoAdapter(object):

    def __init__(self, context):
        self.obj = aq_base(context)
        self.context = context

    def get_infos(self, category):
        filesize = self._filesize
        portal_url = api.portal.get_tool('portal_url')
        infos = {
            'title': self.obj.Title(),
            'description': self.obj.Description(),
            'id': self.obj.getId(),
            'category_uid': category.category_uid,
            'category_id': category.category_id,
            'category_title': category.category_title,
            'subcategory_uid': None,
            'subcategory_id': None,
            'subcategory_title': None,
            'relative_url': portal_url.getRelativeUrl(self.context),
            'download_url': self._download_url,
            'icon_url': utils.get_category_icon_url(category),
            'portal_type': self.obj.portal_type,
            'filesize': filesize,
            'warn_filesize': utils.warn_filesize(filesize),
            'to_print': self._to_print,
            'confidential': self._confidential,
            'preview_status': self._preview_status,
        }
        # update subcategory infos if any
        if ISubcategory.providedBy(category):
            subcategory_infos = {}
            subcategory_infos['subcategory_uid'] = category.UID()
            subcategory_infos['subcategory_id'] = category.getId()
            subcategory_infos['subcategory_title'] = category.Title()
            infos.update(subcategory_infos)
        return infos

    @property
    def _category(self):
        """Return the category instead of the subcategory"""
        return '_-_'.join(self.obj.content_category.split('_-_')[:3])

    @property
    def _download_url(self):
        """Return the download url (None by default) for the current object"""
        url = u'{url}/@@download/{field}/{filename}'
        portal_url = api.portal.get_tool('portal_url')
        if IFile.providedBy(self.obj):
            return url.format(
                url=portal_url.getRelativeUrl(self.context),
                field='file',
                filename=self.obj.file.filename,
            )
        if IImage.providedBy(self.obj):
            return url.format(
                url=portal_url.getRelativeUrl(self.context),
                field='file',
                filename=self.obj.image.filename,
            )

    @property
    def _filesize(self):
        """Return the filesize if the contenttype is a File or an Image"""
        if IFile.providedBy(self.obj):
            return self.obj.file.size
        if IImage.providedBy(self.obj):
            return self.obj.image.size

    @property
    def _to_print(self):
        return getattr(self.obj, 'to_print', False)

    @property
    def _confidential(self):
        return getattr(self.obj, 'confidential', False)

    @property
    def _preview_status(self):
        return IIconifiedPreview(self.obj).status


class CategorizedObjectPrintableAdapter(object):

    def __init__(self, context):
        self.context = context

    @property
    def is_printable(self):
        if ILink.providedBy(self.context):
            return False
        if IFile.providedBy(self.context):
            return IIconifiedPreview(self.context).is_convertible()
        if IImage.providedBy(self.context):
            return True
        return True

    @property
    def error_message(self):
        return u'Can not be printed'

    def update_object(self):
        self.context.to_print_message = None
        if self.is_printable is False:
            # None means 'deactivated'
            self.context.to_print = None
            self.context.to_print_message = self.error_message


class CategorizedObjectAdapter(object):

    def __init__(self, context, request, brain):
        self.context = context
        self.request = request
        self.brain = brain

    def can_view(self):
        return True


class CategorizedObjectPreviewAdapter(object):
    """Base adapter to verify the preview conversion status"""

    def __init__(self, context):
        self.context = context

    @property
    def status(self):
        """
          Returns the conversion status of context.
        """
        # not_convertable or awaiting conversion?
        if not self.is_convertible():
            return 'not_convertable'

        # under conversion?
        ann = IAnnotations(self.context)['collective.documentviewer']
        if 'successfully_converted' not in ann:
            return 'in_progress'

        if not ann['successfully_converted'] is True:
            return 'conversion_error'

        return 'converted'

    @property
    def converted(self):
        """ """
        return self.status == 'converted'

    def is_convertible(self):
        """
          Check if the context is convertible (hopefully).
        """
        # collective.documentviewer add an entry to the annotations
        annotations = IAnnotations(self.context)
        if 'collective.documentviewer' not in annotations.keys():
            Settings(self.context)

        settings = GlobalSettings(api.portal.get())
        return allowedDocumentType(self.context,
                                   settings.auto_layout_file_types)


class IconifiedCategoryGroupAdapter(object):

    def __init__(self, config, context):
        self.config = config
        self.context = context

    def get_group(self):
        return self.config

    def get_every_categories(self):
        return utils.get_categories(self.context)
