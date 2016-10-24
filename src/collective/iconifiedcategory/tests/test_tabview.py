# -*- coding: utf-8 -*-

from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from plone import api
from Products.CMFCore.permissions import ModifyPortalContent
from collective.documentviewer.config import CONVERTABLE_TYPES
from collective.documentviewer.settings import GlobalSettings
from collective.documentviewer.settings import Settings
from collective.iconifiedcategory.browser.tabview import PrintColumn
from collective.iconifiedcategory.browser.tabview import CategorizedContent
from collective.iconifiedcategory.tests.base import BaseTestCase
from collective.iconifiedcategory import utils


class TestCategorizedTabView(BaseTestCase):

    def test_table_render(self):
        view = self.portal.restrictedTraverse('@@iconifiedcategory')
        result = view()
        self.assertTrue('<a href="http://nohost/plone/image" ' in result)
        self.assertTrue('<a href="http://nohost/plone/file" ' in result)
        self.assertTrue('<td>Category 1-1</td>' in result)

        # when nothing to display
        api.content.delete(self.portal['file'])
        api.content.delete(self.portal['image'])
        self.assertEqual(self.portal.categorized_elements, {})
        self.assertTrue('No element to display.' in view())

    def test_table_render_when_preview_enabled(self):
        # enable collective.documentviewer so document is convertible
        gsettings = GlobalSettings(self.portal)
        gsettings.auto_layout_file_types = CONVERTABLE_TYPES.keys()
        # initialize collective.documentviewer annotations on file
        Settings(self.portal['file'])
        Settings(self.portal['image'])
        notify(ObjectModifiedEvent(self.portal['file']))
        notify(ObjectModifiedEvent(self.portal['image']))

        view = self.portal.restrictedTraverse('@@iconifiedcategory')
        result = view()
        self.assertTrue('<a href="http://nohost/plone/image/documentviewer#document/p1" ' in result)
        self.assertTrue('<a href="http://nohost/plone/file/documentviewer#document/p1" ' in result)

    def test_PrintColumn(self):
        table = self.portal.restrictedTraverse('@@iconifiedcategory')
        brain = CategorizedContent(self.portal.portal_catalog(UID=self.portal['file'].UID())[0],
                                   self.portal)
        obj = brain.real_object()
        column = PrintColumn(self.portal, self.portal.REQUEST, table)
        # not convertible by default as c.documentviewer not enabled
        self.assertEqual(
            column.renderCell(brain),
            u'<a href="#" '
            u'class="iconified-action deactivated" '
            u'alt="Not convertible to a printable format" '
            u'title="Not convertible to a printable format"></a>')
        self.assertIsNone(brain.to_print)
        self.assertIsNone(obj.to_print)

        # enable collective.documentviewer so document is convertible
        gsettings = GlobalSettings(self.portal)
        gsettings.auto_layout_file_types = CONVERTABLE_TYPES.keys()
        # initialize collective.documentviewer annotations on file
        Settings(obj)
        # enable to_print management in configuration
        category = utils.get_category_object(obj, obj.content_category)
        category_group = category.get_category_group(category)
        category_group.to_be_printed_activated = True
        category.to_print = False
        notify(ObjectModifiedEvent(obj))
        brain = CategorizedContent(self.portal.portal_catalog(UID=self.portal['file'].UID())[0],
                                   self.portal)
        self.assertEqual(brain.to_print, False)
        self.assertFalse(obj.to_print)
        self.assertEqual(
            column.renderCell(brain),
            u'<a href="http://nohost/plone/file/@@iconified-print" '
            u'class="iconified-action editable" '
            u'alt="Should not be printed" '
            u'title="Should not be printed"></a>')

        # set to_print to True
        obj.to_print = True
        notify(ObjectModifiedEvent(obj))
        brain = CategorizedContent(self.portal.portal_catalog(UID=self.portal['file'].UID())[0],
                                   self.portal)
        self.assertTrue(brain.to_print, False)
        self.assertTrue(obj.to_print)
        self.assertEqual(
            column.renderCell(brain),
            u'<a href="http://nohost/plone/file/@@iconified-print" '
            u'class="iconified-action active editable" '
            u'alt="Must be printed" '
            u'title="Must be printed"></a>')

        # if element is not editable, the 'editable' CSS class is not there
        obj.manage_permission(ModifyPortalContent, roles=[])
        notify(ObjectModifiedEvent(obj))
        self.assertEqual(column.renderCell(brain),
                         u'<a href="http://nohost/plone/file/@@iconified-print" '
                         u'class="iconified-action active" '
                         u'alt="Must be printed" title="Must be printed"></a>')