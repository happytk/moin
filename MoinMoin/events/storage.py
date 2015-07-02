import MoinMoin.events as ev
# import logging

def handle_page_renamed(event):
    # event.page.page_name_fs (saved already)
    event.old_page.delete_page()

def handle_page_deleted(event):
    event.page.delete_page()

def handle_page_reverted(event):
    # name = event.page.page_name
    # logging.info('reverted ' + name + ',' + event.previous + ',' + event.current)
    pass

def handle_page_copied(event):
    # name = event.page.page_name
    # logging.info('copied ' + name)
    pass

def handle(event):
    """An event handler"""

    # if isinstance(event, (ev.PageChangedEvent, ev.TrivialPageChangedEvent)):
    #     return handle_page_change(event)
    if isinstance(event, ev.PageRenamedEvent):
        return handle_page_renamed(event)
    elif isinstance(event, ev.PageDeletedEvent):
        return handle_page_deleted(event)
    elif isinstance(event, ev.PageCopiedEvent):
        return handle_page_copied(event)
    elif isinstance(event, ev.PageRevertedEvent):
        return handle_page_reverted(event)
