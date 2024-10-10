import os.path
from abc import ABC
from dataclasses import dataclass


PROFILE_PHOTO_DIR = os.path.join('users', 'profile', 'photo')
ATTACHMENT_MODEL_DIR = os.path.join('users', 'models', 'attachment')

CONTENT_TYPES = (
    'email',
    'phone',
    'address',
    'link',
    'attachment',
    'award',
    'certificate',
    'license',
    'membership',
    'workexperience',
    'volunteerwork',
    'education',
    'project',
    'publishedwork',
    'patent',
)

CONTENT_CATEGORIES = {
    'Contact Info': [
        'Email',
        'Phone',
        'Address',
    ],
    'Link': [
        'Website',
        'GitHub',
    ],
    'Attachment': [
        'Document',
        'Image',
    ],
    'Professional': [
        'Work Experience',
        'Project',
        'Membership',
        'License',
        'Certificate',
    ],
    'Educational': [
        'Education',
        'Project',
        'Membership',
    ],
    'Achievements': [
        'Published Work',
        'Award',
        'Patent',
    ],
    'Interests': [
        'Volunteer Work',
    ],
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
