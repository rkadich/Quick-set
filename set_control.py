import maya.cmds as cmds
from PySide2 import QtCore, QtGui, QtWidgets
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
import custom_title_bar2 as tb
import os, string
import set_control_ui as ui
import set_control_mel as engine
reload(engine)
reload(ui)
 
# --------------------------------------------------- High DPI monitors adaptation
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
 
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

# -----------------------------------------------Decorators Class
class UserDecorators():
	@classmethod
	def undoable(self, funct):
		def wrapper(*args, **kwargs):
			engine.undo_start()
			result = funct(*args, **kwargs)
			engine.undo_end()
			return result
		return wrapper

#---------------------------------------------Custom toolbar setup
class MyBar(tb.MyBar):
	def __init__(self, parent=None, *args, **kwargs):
		super(MyBar, self).__init__(parent)

		self.layout.setContentsMargins(4,4,4,4)
		self.btn_close.setParent(None)
		self.title.deleteLater()
		self.title = QtWidgets.QLabel(" QUICK SET")
		font = QtGui.QFont()
		font.setFamily("Segoe UI")
		font.setPointSize(7)
		font.setWeight(15)
		font.setBold(True)
		self.title.setStyleSheet("QWidget { font: bold 12px;color:rgba(220,150,30);}")
		self.title.setFont(font)
		self.title.setFixedHeight(15)
		self.title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
		self.layout.addWidget(self.title)
		self.layout.addWidget(self.btn_close, alignment=QtCore.Qt.AlignTop)
		self.custom_button(self.btn_close)

	def custom_button(self, button):
		btn_size = 15
		btn_color = 'rgba(200,200,200)'
		self.bg_color = self.palette().color(QtGui.QPalette.Background).name()
		button.setStyleSheet('''QPushButton {
											border: 1px solid  %s ;
											color: %s ;
											border-radius: 0px;
											background-color:  %s;
											}

								QPushButton:pressed {
											color: 'white' ;
											background-color: %s;

											}
								QPushButton:hover:!pressed {
											color: %s;
											background-color: %s;

											}
										'''
										%(btn_color,btn_color, self.bg_color, btn_color, self.bg_color, btn_color)
										)

		self.btn_close.setFixedSize(btn_size,btn_size)



#-----------------------------------------------------------------UI setup
class Set_control_main(ui.Ui_Sets, QtWidgets.QWidget):

	def __init__(self,  *args, **kwargs):
		super(Set_control_main, self).__init__( *args, **kwargs)

		#-----------------------------------------------------Set up flags and variables
		self.tab_state = []
		self.cleared_sets = []
		self.recent_set = None
		self.del_flag = 0
		self.rename_flag = 0
		self.new_flag = 0
		self.delete_all_flag = 0
		self.clear_all_flag = 0
		self.tab_row_height = 22

		#-------------------------------------------------Create settings
		self.settings = QtCore.QSettings('PixelEmbargo','QuickSet')
		geometry = self.settings.value('geometry', '')
		self.restoreGeometry(geometry)

		#-------------------------------------Add custom toolbar
		self.tlayout = QtWidgets.QVBoxLayout()
		self.title_bar = MyBar(self)
		self.tlayout.addWidget(self.title_bar)
		self.setLayout(self.tlayout)
		self.tlayout.setContentsMargins(0,0,0,0)
		self.tlayout.setObjectName('Main_l')
		# self.tlayout.addStretch(-1)
		self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
		# self.setWindowFlags(QtCore.Qt.Tool)
		self.pressing = False

		#-----------------------------------------------------Startup
		self.setupUi(self)
		self.setMinimumSize(150, 180)
		self.resize(180, 250)
		self.my_timer()
		self.scene_items = engine.scene_items()
		# self.set_triggers()
		self.setWindowTitle('Quick set')


		


	#----------------------------------------------------------------Apply CSS File
		dirpath = os.path.dirname(os.path.abspath(__file__))
		css_file = 'scheme.qss'
		# join and fix slashes direction
		scheme_path = os.path.abspath(os.path.join(dirpath, css_file ))
		style_sheet_file = open(scheme_path).read()
		self.setStyleSheet(style_sheet_file)

	#--------------------------------------------------------Customize UI
	def setupUi(self, Sets ):
		super(self.__class__, self).setupUi(Sets)

		self.setObjectName("my_set_ui")
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		# mylabel= QtWidgets.QLabel('BLA')
		# self.tlayout.addWidget(mylabel)
		# spacerItem = QtWidgets.QSpacerItem(700, 2, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		# self.tlayout.addItem(spacerItem)

		self.tlayout.addLayout(self.verticalLayout)

		#-------------------------------------Assign icons
		icon_buttons = {
						self.b_remove : 'remove.png',
						 self.b_clear : 'clear.png',
						   self.b_add : 'add.png', 
						self.b_color : 'color.png',
						self.b_menu : 'menu.png',
						self.b_delete : 'delete.png'
						}
		{self.add_icon(k, v) for k, v in icon_buttons.items()}

		#------------------------------------------Set tool tips
		self.b_add.setToolTip('Add to set')
		self.b_remove.setToolTip('Remove from set')
		self.b_new.setToolTip('Create new set')
		self.b_clear.setToolTip('Clear selected set')
		self.b_delete.setToolTip('Delete')
		self.b_color.setToolTip('Assign color')
		self.b_menu.setToolTip('Extra functions')

		#---------------------------------------Button functions
		self.b_new.clicked.connect(self.new_set)
		self.b_select.clicked.connect(lambda : engine.select_set(self.recent_set))
		self.b_add.clicked.connect(lambda : self.add_to(self.recent_set))
		self.b_remove.clicked.connect(lambda : self.remove_from(self.recent_set))
		self.b_clear.clicked.connect(lambda : self.clear_set(self.recent_set))
		self.b_delete.clicked.connect(lambda : self.delete_set(self.recent_set))
		self.b_menu.released.connect(self.menu_build)
		self.b_color.released.connect(self.color_menu)
		table = self.tableWidget
		table.itemSelectionChanged.connect(self.set_current)

		#---------------------------------------Assign right click menu
		table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		# table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
		table.customContextMenuRequested.connect(self.menu_build)

		#-----------------------------------------Rename Set function
		QtCore.QObject.connect(table, QtCore.SIGNAL("cellChanged(int, int)"), self.rename)

		#-----------------------------------------Table Settings

		
		# # Enable drag & drop ordering of items.
		table.setDragEnabled(False)
		# table.setAcceptDrops(True)
		# table.viewport().setAcceptDrops(True)
		# table.setDragDropOverwriteMode(False)
		# table.setDropIndicatorShown(True)
		# table.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
		table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		 
		#table.setColumnWidth(0, 140)
		table.setColumnWidth(1, 40)
		header = table.horizontalHeader()
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
		#header.setStretchLastSection(True)
		#-------------------Remove blue Focus Border
		table.setFocusPolicy(QtCore.Qt.NoFocus)
		

		self.set_list = engine.set_list()
		self.build_tab(table)


	def add_icon(self, button, img):
		button.setFlat(True)
		button.setObjectName('b_icon')
		dirpath = os.path.dirname(os.path.abspath(__file__))
		iconpath = os.path.join(dirpath,"icons", img)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconpath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		button.setIcon(icon)


		# tb = QtGui.QBrush(QtCore.Qt.transparent)
		#button.setPalette(QtGui.QPalette(tb,tb,tb,tb,tb,tb,tb,tb,tb))




	#--------------------------------------------------UI functions

	def new_set(self):
		self.recent_set = engine.new_set()
		self.set_list.append(self.recent_set)
		table = self.tableWidget
		new_row_id = table.rowCount()
		self.table_item(table, self.recent_set, new_row_id)
		# self.build_tab(table)
		try:
			print self.recent_set
			current = table.findItems(self.recent_set, QtCore.Qt.MatchExactly)
			table.setCurrentItem(current[0])
			# self.set_button_text(self.b_select, current[0].text())
		except Exception as e:
			print str(e)
		self.new_flag = 1
		return self.recent_set


	def add_to(self, q_set):
		if q_set:
			engine.add_to(q_set)
			self.update_value(q_set)
			return
		return engine.warning_msg('Please, select a set or create a new one')

	def remove_from(self, q_set):
		engine.remove_from(q_set)
		self.update_value(q_set)


	@UserDecorators.undoable
	def clear_set(self, q_set):
		engine.clear_set(q_set)
		self.cleared_sets.append(q_set)
		self.update_value(q_set)


	@UserDecorators.undoable
	def delete_set(self, q_set):
		#-------------------------delete selected from widget
		table = self.tableWidget
		try:
			self.deselect(q_set)
			engine.delete_set(q_set)
		except:
			pass
		self.set_list.remove(q_set)
		current = table.findItems(q_set, QtCore.Qt.MatchExactly)
		row = table.row(current[0])
		table.removeRow(row)
		#-------------------------make new selection recent item
		currItem = table.currentItem()
		try:
			currItem.setSelected(True)
			self.recent_set = currItem.text()
			btn_text = currItem.text()
		except:
			btn_text = 'Select'
			pass
		# self.set_button_text(self.b_select, btn_text)
		self.del_flag = 1


	def deselect(self, q_set):
		curr_sel = engine.curr_selection()
		curr_set = engine.in_set(q_set)
		if curr_set == curr_sel:
			engine.clear_selection()



	def update_value(self, q_set):
		table = self.tableWidget
		for i in q_set:
			current = table.findItems(i, QtCore.Qt.MatchExactly)
			for c in current:
				row = table.row(c)
				curr_item = table.item(row, 0).text()
				self.set_value(table, row, curr_item)


	def set_value(self, table, row, item):
		set_items = engine.in_set(item)
		if  not set_items:
			value = '0'
			text_color = '#cfcfa76e'
		else:
			value = str(len(set_items))
			text_color = '#d5d3cf'
		value_item = QtWidgets.QTableWidgetItem(value)
		value_item.setTextAlignment(QtCore.Qt.AlignCenter| QtCore.Qt.AlignVCenter )
		value_item.setForeground(QtGui.QBrush((QtGui.QColor(text_color))))
		value_item.setFlags(
						  QtCore.Qt.ItemIsEnabled | 
						  QtCore.Qt.ItemIsSelectable
						 )

		table.setItem(row,1,value_item)


	def build_tab(self, table):
		table = self.tableWidget
		table.blockSignals(True)
		table.clear()
		table.setRowCount(0)
		[self.table_item(table, x, ind) for ind, x in enumerate(self.set_list)]
		table.blockSignals(False)


	def table_item(self, table, item, ind):
		table.insertRow(ind)
		table.setRowHeight(ind, self.tab_row_height)
		name_item = QtWidgets.QTableWidgetItem(item)
		name_item.setIcon(QtGui.QIcon(':connect24_NEX.png'))
		name_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter )
		# name_item.setFlags(
		# 				  QtCore.Qt.ItemIsEnabled | 
		# 				  QtCore.Qt.ItemIsSelectable | 
		# 				  QtCore.Qt.ItemIsEditable
		# 				 )
		table.setItem(ind,0,name_item)
		self.set_value(table, ind, item)


	# def set_button_text(self, button, text):
	# 	button_width = button.size().width()
	# 	font = QtGui.QFont("times", 24)
	# 	font = button.property("font")
	# 	metrix = QtGui.QFontMetrics(font)
	# 	elidedText = metrix.elidedText(text, QtCore.Qt.ElideRight, button_width-6)
		# button.setText(elidedText)



	def set_current(self):
		items = [i.text() for i in self.tableWidget.selectedItems()][::2]
		print 'Current:', items
		self.recent_set = items
		# self.set_button_text(self.b_select, items)
		# engine.component_select(items)


	def rename(self, edit_row, edit_col):
		table = self.tableWidget
		# ------------------fix row height change bug
		table.setRowHeight(edit_row, self.tab_row_height)
		# ---------rename only if name was changed,not value
		if edit_col != 1:
			# rename only if there was a change in the cell text, not the cell position
			if set(self.tab_items()) != set(self.tab_state):
				# get name input
				name_input = table.item(edit_row, 0).text()
				#check the name validity, fix it if needed and write fixed name into the tab cell
				new_name = self.make_valid(name_input)
				table.blockSignals(True)
				if name_input != new_name:
					table.item(edit_row, edit_col).setText(new_name)
				table.blockSignals(False)
				#rename the set
				engine.set_rename(self.recent_set, new_name)
				#update data
				self.set_list = engine.set_list()
				self.recent_set = table.currentItem().text()
				# self.set_button_text(self.b_select,new_name)
				self.rename_flag = 1


	def tab_items(self):
			table = self.tableWidget
			rows_count = table.rowCount()
			return [table.item(row, 0).text() for row in range(rows_count)]



	def make_valid(self, name_input):
		def len_check(name):
			if len(name) == 0:
				return self.recent_set
			return name

		new_name = name_input.strip()
		valid_chars = "_{}{}".format(string.ascii_letters, string.digits)
		while True:
			new_name = len_check(new_name)
			if new_name[0] not in string.ascii_letters: new_name = new_name[1:]
			else:
				break
		new_name = ''.join([x if x in valid_chars else '_' for x in new_name ])
		return new_name


	def update(self):

		self.tab_state = self.tab_items()
		
		#----------------------------------------------if no changes in sets stop here
		if self.rename_flag == 1:
			print 'Set renamed'
			self.scene_items = engine.scene_items()
			self.rename_flag = 0
			return
		#---------------------------------------------if renamed stop here
		if self.new_flag == 1:
			print 'new Set created'
			self.scene_items = engine.scene_items()
			self.new_flag = 0
			return
		#---------------------------------------------if new set created stop here

		if self.del_flag == 1:
			self.del_flag = 0
			self.scene_items = engine.scene_items()
			print 'Set deleted'
			return

		if self.delete_all_flag == 1:
			self.scene_items = engine.scene_items()
			self.delete_all_flag = 0
			print ' Batch delete '
			return


		if  self.clear_all_flag == 1:
				self.clear_all_flag = 0
				self.scene_items = engine.scene_items()
				print ' Batch clear '
				return

		if self.cleared_sets:
			for q_set in self.cleared_sets:
				if not engine.set_exists(q_set):
					self.cleared_sets.remove(q_set)
				elif engine.set_size(q_set) == 0:
					pass
				else:
					self.update_value(q_set)
					self.cleared_sets.remove(q_set)
					#print 'set is updated'

		if  not self.scene_changed():
			return

		#----------------------------------------------if no changes in scene stop here
		if not self.sets_changed():
			print 'new objects in scene, same sets though, updating table....'
			[self.update_value(q_set) for q_set in engine.set_list()]
			self.scene_items = engine.scene_items()
			return
		#----------------------------------------- if sets deleted in plugin stop here
		print ' sets changed in Maya'
		self.maya_changes()
		self.del_flag = 0
		self.scene_items = engine.scene_items()


	def scene_changed(self):
		current_items = engine.scene_items()
		return current_items != self.scene_items


	def sets_changed(self):
		old_set_list = self.set_list
		new_set_list = engine.set_list()
		return old_set_list != new_set_list


	def returnNotMatches(self, a, b):
			return [[x for x in a if x not in b], [x for x in b if x not in a]]


	def maya_changes(self):
		table = self.tableWidget
		old_set_list = self.set_list
		new_set_list = engine.set_list()
		changed_sets = self.returnNotMatches(new_set_list, old_set_list)
		new_sets = changed_sets[0][::-1] #reversed order
		deleted_sets = changed_sets[1]
		# print 'DELETED >>>>>', deleted_sets
		# print 'NEW>>>>', new_sets
		if deleted_sets:
			[self.delete_set(q_set) for q_set in deleted_sets if deleted_sets ]
		if new_sets: 
			[self.set_list.append(x) for x in new_sets]
			self.build_tab(table)
		[self.update_value(q_set) for q_set in engine.set_list()]



	#def item_clicked(self):


	# #------------------------------------------------------Script Jobs setup
	# def set_triggers(self):
	# 	self.trigger_delete = cmds.scriptJob(
	# 									p="my_set_ui",
	# 									ct=['delete',self.tab_refresh],
	# 									killWithScene=False,
	# 									replacePrevious=False
	# 									)

		# self.trigger_undo = cmds.scriptJob(
		# 								p="my_set_ui",
		# 								event =['Undo', self.rebuild_tab],
		# 								killWithScene=False,
		# 								replacePrevious=False
		# 								)


	#-------------------------------------------------------Right click menu

	def menu_build(self):
		menu_tools = dict((
							#('refresh list', self.refresh_list),
							('clear all sets', self.clear_all),
							('delete empty sets', self.delete_empty),
							('delete all sets', self.delete_all),
							))

		table = self.tableWidget
		self.menu = QtWidgets. QMenu(table)
		[self.add_menu_item(k, menu_tools[k]) for k, v in menu_tools.items()]
		popup_point = QtGui.QCursor.pos()
		self.menu.popup(popup_point)


	def add_menu_item(self, item_name, my_function):
		table = self.tableWidget
		icon = self._icon(item_name)
		new_item = QtWidgets.QAction(icon, item_name, table)
		new_item.triggered.connect(my_function)
		self.menu.addAction(new_item)


	def _icon(self, item_name):
		icon_hash = dict((
							('refresh list', 'clear_all'),
							('clear all sets', 'clear_all'),
							('delete empty sets', 'delete_empty'),
							('delete all sets', 'delete_all'),
							))

		dirpath = os.path.dirname(os.path.abspath(__file__))
		ic_file = '{}.{}'.format(icon_hash[item_name],'png')
		iconpath = os.path.join(dirpath,"icons",ic_file)
		return QtGui.QIcon(iconpath)

	#------------------color choser menu
	def color_menu(self):
		menu_colors = ('red', 'green', 'yellow', 'cyan', 'pink')

		#---------------------------Blend menu colors
		palette = self.palette()
		base_clr = palette.base().color()
		print base_clr
		clrs_blended = [self.blendColors(base_clr, QtGui.QColor(i), ratio=0, alpha=150) for i in menu_colors]
		clrs_blended.insert(0, base_clr)
		print 'blended clrs>>', clrs_blended

		table = self.tableWidget
		self.cmenu = QtWidgets. QMenu(table)
		self.cmenu.setFixedWidth(30)
		self.cmenu. setStyleSheet(''' QMenu::icon { padding-left: 0px;	
												   padding-right: 0px;
												   margin: 0px;
												   border: 1px solid grey;
												  }
									  QMenu::item { padding-left: 10px;
									  				}
												   ''')
		[self.add_color_item (i, self.assign_color ) for i in clrs_blended]
		# popup_point = QtGui.QCursor.pos()
		popup_point = self.mapToGlobal( self.b_color.pos() )
		self.cmenu.popup(popup_point)


	def assign_color(self, color ):
		# color = QtGui.QColor('green')
		table = self.tableWidget
		rows_selected = table.selectedItems()
		for r in rows_selected:
			r.setBackground(color)

	
	def add_color_item(self, item_color, my_function):
		table = self.tableWidget
		empty=None
		#-------------------------Create pixmap for color
		pixmap = QtGui.QPixmap(26,26)
		print 'item color>>>', item_color
		pixmap.fill(item_color)
		#----------------------------------------
		new_item = QtWidgets.QAction(pixmap, empty, table)
		new_item.triggered.connect(lambda: my_function(item_color))

		self.cmenu.addAction(new_item)



	def blendColors(self, first, second, ratio=0.5, alpha=100):
		ratio2 = 1 - ratio
		return QtGui.QColor(
			(first.red() * ratio) + (second.red() * ratio2),
			(first.green() * ratio) + (second.green() * ratio2),
			(first.blue() * ratio) + (second.blue() * ratio2),
			alpha,
			)


	@UserDecorators.undoable
	def clear_all(self):
		[self.clear_set(s) for s in engine.set_list() ]
		self.clear_all_flag = 1


	@UserDecorators.undoable
	def delete_empty(self):
		[self.delete_set(s) for s in engine.set_list() if engine.set_size(s) == 0 ]
		self.del_flag = 0
		self.delete_all_flag = 1


	@UserDecorators.undoable
	def delete_all(self):
		[self.delete_set(s) for s in engine.set_list()]
		self.del_flag = 0
		self.delete_all_flag = 1


	def refresh_list(self):
		table = self.tableWidget
		self.set_list = engine.set_list()
		self.build_tab(table)

	#-------------------------------------------------------Timer
	def my_timer(self):
		#stop previous timer
		self.stop_timer()
		# every 0,5 seconds check for scene changes
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(500)

	def stop_timer(self):
		try:
			self.timer.stop()
		except:
			pass



	#-----------------------------------------------Close event
	def closeEvent(self, event):
		# cmds.scriptJob( kill=Set_control_window.trigger_undo, force=True )
		# cmds.scriptJob( kill=Set_control_window.trigger_set_mod, force=True )
		# print 'Sets control closed'
		geometry = self.saveGeometry()
		self.settings.setValue('geometry', geometry)
		self.stop_timer()
		Set_control_window.deleteLater()
		return super( QtWidgets.QDialog, self ).closeEvent( event )




#--------------------------------------------------------------------

def maya_main_window():
		main_window_ptr = omui.MQtUtil.mainWindow()
		return wrapInstance(long(main_window_ptr), QtWidgets.QMainWindow)


def show():
	#---------------------------------------------------Close Cargo window if exists
	global Set_control_window
	try:
		Set_control_window.close()
	except:
		pass

	Set_control_window = Set_control_main(parent=maya_main_window())
	Set_control_window.show()                  #open window

#show()
