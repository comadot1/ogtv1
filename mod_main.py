from tool import ToolUtil

from .setup import *
from .ogtv_handle import ogtv


class ModuleMain(PluginModuleBase):

    def __init__(self, P):
        super(ModuleMain, self).__init__(P, name='main', first_menu='list')


    def process_menu(self, page_name, req):
        arg = P.ModelSetting.to_dict()
        arg['api_m3u'] = ToolUtil.make_apikey_url(f"/{P.package_name}/api/m3u")
        return render_template(f'{P.package_name}_{self.name}_{page_name}.html', arg=arg)
    
    
    def process_command(self, command, arg1, arg2, arg3, req):
        if command == 'broad_list':
            ret = {'ret':'success', 'ch_list':ogtv.ch_list()}
        elif command == 'play_url':
            url = ToolUtil.make_apikey_url(f"/{P.package_name}/api/url.m3u8?ch_id={arg1}")
            ret = {'ret':'success', 'data':url}
        return jsonify(ret)


    def process_api(self, sub, req):
        try:
            if sub == 'm3u':
                return ogtv.make_m3u()
            elif sub == 'url.m3u8':
                mode, data = ogtv.get_m3u8(req.args.get('ch_id'))
                if mode == 'text':
                    return data
                else:
                    return redirect(data)
            elif sub == 'segment.ts':
                return ogtv.segment(req)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())

