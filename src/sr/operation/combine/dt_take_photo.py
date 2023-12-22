from basic.i18_utils import gt
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_TAKE_PHOTO
from sr.context import Context
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.menu.click_phone_menu_item_at_right import ClickPhoneMenuItemAtRight
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.menu.take_photo import TakePhoto


class DtTakePhoto(StatusCombineOperation2):

    def __init__(self, ctx: Context):
        """
        每日实训 - 拍照
        需要在大世界非战斗情况下使用
        :param ctx:
        """
        open_menu = StatusCombineOperationNode(node_id='open_menu', op=OpenPhoneMenu(ctx))
        click_photo = StatusCombineOperationNode(node_id='click_photo', op=ClickPhoneMenuItemAtRight(ctx, phone_menu_const.PHOTO))
        take_photo = StatusCombineOperationNode(node_id='take_photo', op=TakePhoto(ctx))
        back = StatusCombineOperationNode(node_id='back', op=BackToWorld(ctx))

        edges = [
            StatusCombineOperationEdge2(node_from=open_menu, node_to=click_photo),
            StatusCombineOperationEdge2(node_from=click_photo, node_to=take_photo),
            StatusCombineOperationEdge2(node_from=take_photo, node_to=back)
        ]

        super().__init__(ctx, op_name='%s %s' % (gt('实训任务', 'ui'), gt(MISSION_TAKE_PHOTO.id_cn, 'ui')),
                         edges=edges
                         )