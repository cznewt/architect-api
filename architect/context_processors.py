
def base(request):
    if request.is_ajax():
        template_base = 'modal_base.html'
    else:
        template_base = 'content_base.html'
    return {
        'TEMPLATE_BASE': template_base,
        'XHR_REQUEST': request.is_ajax(),
    }
