import maya.cmds as cmds
import maya.mel as mel
#make selection:

default_sets = ['defaultLightSet', 'defaultObjectSet', 'initialParticleSE', 'initialShadingGroup']
name_filters = ['modelPanel', 'topoSymmetry']


def new_set():
	selection = make_list()
	new_set =  cmds.sets( selection, name='QuickSet_#' )
	return cmds.sets(e=True, fl=new_set )


def add_to(m_set):
	selection = make_list()
	return [cmds.sets( selection, e=True, include=s ) for s in m_set]


def remove_from(m_set):
	selection = make_list()
	return [cmds.sets( selection, e=True, remove=s ) for s in m_set]


def clear_set(m_set):
	return [cmds.sets( e=True, clear=s ) for s in m_set]


def delete_set(m_set):
	return cmds.delete(m_set)


def in_set( m_set ):
	return sorted(cmds.ls(cmds.sets( m_set, q=True ),fl=True))


def make_list():
	selection = cmds.ls(sl=1, fl=1)
	selection = list(set(selection))
	return sorted(selection)


def select_set(selection_set):
	return cmds.select(selection_set, r=1)


def set_exists( m_set ):
	return m_set in set_list()


def set_list():
	#default_sets = ['defaultLightSet', 'defaultObjectSet', 'initialParticleSE', 'initialShadingGroup']
	shading_groups = cmds.ls(type='shadingEngine')
	exclude_group = list(set(default_sets + shading_groups))
	curr_sets = [x for x in cmds.ls(sets=True, mat=False) if x not in exclude_group ]
	for x in name_filters:
		curr_sets = filter_by_name(curr_sets, x)
	return curr_sets


def filter_by_name(set_list, my_filter):
	return [x for x in set_list if my_filter not in x]


def set_rename(m_set, new_name):
	return cmds.rename( m_set, new_name )


def set_size(m_set):
	return len(in_set(m_set))


def warning_msg(msg):
	cmds.warning( msg )


def scene_items():
	return cmds.ls()


def curr_selection():
	return sorted(cmds.ls(sl=1, fl=1))


def clear_selection():
	#object_selection_mode()
	cmds.select(clear=True)


def component_select(selection_set):
	# if set is  already selected, don't select again
	now_selected = cmds.ls(sl=1,fl=1)
	if sorted(now_selected) == sorted(in_set(selection_set)):
		return

	clear_selection()
	mode = max_component(selection_set)
	s_modes = { 
				'vertices':'vertex', 
				'edges': 'edge', 
				'faces':'facet' 
			   }


	if mode not in ('objects', None ):
		curr_object = current_object()
		cmds.select(curr_object, r = True)
		cmds.selectMode( component=True)

		command = '''selectType -alc 0 -{} 1;'''.format(s_modes[mode] )
		mel.eval(command)
		select_set(selection_set)
	else:
		object_selection(selection_set)
	


def object_selection(selection_set):
	try:
		curr_object = current_object()
		mel.eval(command)
	except:
		pass

	select_set(selection_set)
	cmds.selectMode( object=True)


def current_object():
	selected = cmds.ls(sl=1,fl=1)
	selected_list = [x.split('.')[0] for x in selected]
	return selected_list[0]	



def max_component(selection_set):
	select_set(selection_set)
	if cmds.ls(sl=1):
		s_modes = {12:'objects', 31:'vertices', 32:'edges', 34:'faces' }
		cur_sel = {v:cmds.filterExpand( sm=k ) for k, v in s_modes.items() if cmds.filterExpand( sm=k )}
		try:
			biggest_group = max(cur_sel.values(), key=len)
			return cur_sel.keys()[cur_sel.values().index(biggest_group)]
		except: pass


def undo_start():
	return cmds.undoInfo(openChunk=True)

def undo_end():
	return cmds.undoInfo(closeChunk=True)



# selection_set = new_set()
# selection_set = add_to(selection_set)
# selection_set = remove_from(selection_set)
# selection_set = clear_set(selection_set)
#cmds.select(selection_set, r=1)