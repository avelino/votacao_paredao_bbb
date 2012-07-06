from london.websockets import websocket

@websocket
def ws_handler(request, message=None, opening=False, closing=False):
    print opening, closing
    if not opening and not closing:
        print (message,)
        if message.lower().strip() == 'close':
            request.close_websocket()
        else:
            return message.upper()

