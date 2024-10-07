import os.path
from abc import ABC
from dataclasses import dataclass


PROFILE_PHOTO_DIR = os.path.join('users', 'profile', 'photo')
MEDIA_MODEL_DIR = os.path.join('users', 'models', 'media')
VCARD_DIR = os.path.join('users', 'vcard')

CONTENT_TYPES = (
    'email',
    'phone',
    'address',
    'link',
)

CONTENT_CATEGORIES = {
    'Contact Info': [
        'Email',
        'Phone',
        'Address',
    ],
    'Link': [
        'Website',
        'GitHub'
    ],
    'Media': [
        'Document',
        'Image',
        'Audio',
        'Video',
    ]
}


class ContentCategories:
    categories = [
        'ContactInfo',
        'Link',
    ]

    @dataclass
    class Category:
        display_name: str
        is_app: bool
        contents: list

        @property
        def name(self):
            return ''.join(self.display_name.split())

        def __iter__(self):
            return iter(self.contents)

        def __len__(self):
            return len(self.contents)

    def __iter__(self):
        return (getattr(self, c) for c in self.categories)

    ContactInfo = Category(
        display_name='Contact Info',
        is_app=False,
        contents=[
            'Email',
            'Phone',
            'Address',
        ],
    )

    Link = Category(
        display_name='Link',
        is_app=True,
        contents=[
            'Website',
            'GitHub',
        ]
    )
