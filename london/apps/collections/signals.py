from london.dispatch import Signal
from london.apps.collections import add_collection_items_to_sender_form, save_collection_items_from_sender_form


collections_form_initialize = Signal()
collections_form_initialize.connect(add_collection_items_to_sender_form)
collections_form_pre_save = Signal()
collections_form_post_save = Signal()
collections_form_post_save.connect(save_collection_items_from_sender_form)
collections_form_clean = Signal()