from sr import performance_recorder
from sr.app.routine.forgotten_hall_app import ForgottenHallApp, ForgottenHallTeamModule
from sr.const.character_const import QUANTUM, ICE, SILVERWOLF, FUXUAN, JINGLIU, PELA, SEELE, TINGYUN, \
    DANHENGIMBIBITORLUNAE, LUOCHA, YUKONG, CLARA, ASTA, FIRE, WIND, IMAGINARY, LIGHTNING, CHARACTER_COMBAT_TYPE_LIST, \
    HUOHUO, PHYSICAL, HANYA


def _test_search_best_mission_team():
    m01 = ForgottenHallTeamModule(module_name='银狼符玄插件', combat_type='', module_type='',
                                  character_id_list=[SILVERWOLF.id, FUXUAN.id])
    m03 = ForgottenHallTeamModule(module_name='镜流', combat_type='', module_type='',
                                  character_id_list=[JINGLIU.id, PELA.id])
    m04 = ForgottenHallTeamModule(module_name='龙丹', combat_type='', module_type='',
                                  character_id_list=[DANHENGIMBIBITORLUNAE.id, LUOCHA.id])
    m05 = ForgottenHallTeamModule(module_name='龙丹4人', combat_type='', module_type='',
                                  character_id_list=[DANHENGIMBIBITORLUNAE.id, HANYA.id, YUKONG.id, LUOCHA.id])
    m06 = ForgottenHallTeamModule(module_name='克拉拉', combat_type='', module_type='',
                                  character_id_list=[CLARA.id, TINGYUN.id, YUKONG.id, LUOCHA.id])

    m91 = ForgottenHallTeamModule(module_name='符玄', combat_type='', module_type='',
                                  character_id_list=[FUXUAN.id])
    m92 = ForgottenHallTeamModule(module_name='罗刹', combat_type='', module_type='',
                                  character_id_list=[LUOCHA.id])
    m93 = ForgottenHallTeamModule(module_name='银狼', combat_type='', module_type='',
                                  character_id_list=[SILVERWOLF.id])
    m94 = ForgottenHallTeamModule(module_name='佩拉', combat_type='', module_type='',
                                  character_id_list=[PELA.id])
    m95 = ForgottenHallTeamModule(module_name='驭空', combat_type='', module_type='',
                                  character_id_list=[YUKONG.id])
    m96 = ForgottenHallTeamModule(module_name='停云', combat_type='', module_type='',
                                  character_id_list=[TINGYUN.id])
    m97 = ForgottenHallTeamModule(module_name='艾丝妲', combat_type='', module_type='',
                                  character_id_list=[ASTA.id])
    m98 = ForgottenHallTeamModule(module_name='寒鸦', combat_type='', module_type='',
                                  character_id_list=[HANYA.id])

    module_list = [
        m01, m03, m04, m05, m06,
        m91, m92, m93, m94, m95, m96, m97, m98
    ]

    for type1 in CHARACTER_COMBAT_TYPE_LIST:
        for type2 in CHARACTER_COMBAT_TYPE_LIST:
            node1_combat_type = [IMAGINARY, WIND]
            node2_combat_type = [WIND, LIGHTNING, QUANTUM]
            node_combat_types = [node1_combat_type, node2_combat_type]
            node_team_list = ForgottenHallApp.search_best_mission_team(node_combat_types, module_list)
            cn_list = []
            for node_team in node_team_list:
                cn_list.append([c.cn for c in node_team])
            print(type1)
            print(type2)
            print(cn_list)
            break
        break

    print(performance_recorder.get('search_best_mission_team'))


if __name__ == '__main__':
    _test_search_best_mission_team()