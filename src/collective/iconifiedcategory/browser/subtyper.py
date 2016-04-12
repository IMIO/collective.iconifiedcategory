# -*- coding: utf-8 -*-
"""
collective.iconifiedcategory
----------------------------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from Acquisition import aq_base
from Products.Five import BrowserView
from zope.interface import implements

from collective.iconifiedcategory.interfaces import IIconifiedCategorySubtyper


class IconifiedCategoryPublicSubtyper(BrowserView):
    implements(IIconifiedCategorySubtyper)

    def __init__(self, context, request):
        self.context = aq_base(context)
        self.request = request

    @property
    def have_categorized_elements(self):
        """See IIconifiedCategorySubtyper"""
        return False


class IconifiedCategorySubtyper(IconifiedCategoryPublicSubtyper):

    @property
    def have_categorized_elements(self):
        """See IIconifiedCategorySubtyper"""
        return len(getattr(self.context, 'categorized_elements', {})) > 0