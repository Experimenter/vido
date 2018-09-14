#!/usr/bin/env python
import gi, os.path, sys
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from subprocess import *
from tempfile import gettempdir

try:
    os.chdir('/'.join(sys.argv[0].split('/')[0:-1]))
except:
    pass

class vidoMain:

    def __init__( self ):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("vido.glade")

        self.winmain = self.builder.get_object("vidoMain")
        self.listUrl=self.builder.get_object("listUrl")
        self.txtUrl=self.builder.get_object("txtUrl")
        self.progressbar=self.builder.get_object("progressbar")
        self.statusbar=self.builder.get_object("statusbar")
        self.folderDownload=self.builder.get_object("folderDownload")
        self.cboFormat=self.builder.get_object("cboFormat")
        self.txtProxy=self.builder.get_object("txtProxy")
        self.txtProxyUser=self.builder.get_object("txtProxyUser")
        self.txtProxyPass=self.builder.get_object("txtProxyPass")
        self.txtUname=self.builder.get_object("txtUname")
        self.txtPass=self.builder.get_object("txtPass")

        self.progress=self.builder.get_object("lblProgress")
        self.btnDownload=self.builder.get_object("btnDownload")
        self.btnClear=self.builder.get_object("btnClear")
        self.status_context_id = self.statusbar.get_context_id('download status')


        dic={
            "quit": self.quit,
            "btnAdd_clicked": self.btnAdd_clicked,
            "btnReload_clicked": self.btnReload_clicked,
            "btnPause_clicked": self.btnPause_clicked,
            "btnDelete_clicked": self.btnDelete_clicked,
            "btnUp_clicked": self.btnUp_clicked,
            "btnDown_clicked": self.btnDown_clicked,
            "btnClear_clicked": self.btnClear_clicked,
            "btnDrop_clicked": self.btnDrop_clicked,
            "btnCancel_clicked": self.btnCancel_clicked,
            "btnDownload_clicked": self.btnDownload_clicked,
            "btnSave_clicked": self.btnSave_clicked,
            "folderDownload_changed": self.folderDownload_changed
        }
        self.builder.connect_signals(dic)

        self.winmain.connect("delete-event", self.quit)
        self.statusicon = Gtk.StatusIcon()
        self.statusicon.set_from_file('vido.svg')
        self.statusicon.connect('activate', self.status_clicked)
        self.statusicon.set_tooltip_text("Vido")
        self.iconified = False

        self.init_droparea()

        # set local appdir to save pref and url list, create if doesn't exist
        self.local_appdir = os.path.expanduser('~/.config') + "/vido/"
        if not os.path.exists(self.local_appdir):
            os.makedirs(self.local_appdir)

        #set pref and url file vars
        self.pref_file = self.local_appdir + "prefs"
        self.url_file = self.local_appdir + "urllist"

        self.__init_ui__()
        #load preferences and url list
        self.__load_preferences__()
        self.__load_url_list__()

    def quit(self, widget, data=None):
        self.btnCancel_clicked(None)
        exit()

    def btnAdd_clicked(self, widget, data=None):
        url = self.txtUrl.get_text()
        if url.strip()!="":
            self.listUrl.get_model().append(["Queued",self.txtUrl.get_text(),''])
            self.txtUrl.set_text("")
        self.__save_url_list__()

    def btnReload_clicked(self, widget, data=None):
        url_model, url_selected = self.listUrl.get_selection().get_selected_rows()
        for url in url_selected:
            if url_model[url][0]!="Processing":
                url_model[url][0] = "Queued"
        self.__save_url_list__()

    def btnPause_clicked(self, widget, data=None):
        url_model, url_selected = self.listUrl.get_selection().get_selected_rows()
        for url in url_selected:
            if url_model[url][0]=="Queued":
                url_model[url][0] = "Paused"
        self.__save_url_list__()

    def btnDelete_clicked(self, widget, data=None):
        url_model, url_selected = self.listUrl.get_selection().get_selected_rows()
        iters = [url_model.get_iter(url) for url in url_selected]
        for iter in iters:
            if url_model[iter][0]!="Processing":
                url_model.remove(iter)
        self.__save_url_list__()

    def btnUp_clicked(self, widget, data=None):
        url_model, url_selected = self.listUrl.get_selection().get_selected_rows()

        for url in url_selected:
            if url[0]<=0 : break
            iter = url_model.get_iter(url)
            iter_prev = url_model.get_iter(url[0]-1)
            url_model.move_before(iter,iter_prev)

        self.__save_url_list__()

    def btnDown_clicked(self, widget, data=None):
        url_model, url_selected = self.listUrl.get_selection().get_selected_rows()

        for url in url_selected[::-1]:
            iter = url_model.get_iter(url)
            iter_next = url_model.iter_next(iter)
            if iter_next == None: break
            url_model.move_after(iter,iter_next)

        self.__save_url_list__()

    def btnClear_clicked(self, widget, data=None):
        self.listUrl.get_model().clear()
        self.__save_url_list__()

    def btnDrop_clicked(self, widget, data=None):
        if self.w.get_property('visible'):
            self.pos = self.w.get_position()
            self.w.hide()
        else:
            try:
                self.w.move(self.pos[0],self.pos[1])
            except:
                pass
            self.w.show_all()
        return True

    def btnCancel_clicked(self, widget, data=None):
        self.__reset__("Queued","User Abort")

    def btnDownload_clicked(self, widget, data=None):
        self.current_url = self.__next_url__()
        if not self.current_url: return
        self.btnDownload.set_sensitive(False)
        self.btnClear.set_sensitive(False)
        self.listUrl.set_reorderable(False)
        location = self.folderDownload.get_current_folder()
        vido_cmd = ["youtube-dl", "--output=%(title)s_%(height)s.%(ext)s", "-c","--no-playlist"]+self.__download_params__()
        vido_cmd.append(self.current_url[1])
        print (vido_cmd) #print parameters for inspection
        self.file_stdout = open(gettempdir()+'/vido.txt', 'w')
        self.proc = Popen(vido_cmd,  stdout=self.file_stdout, stderr=STDOUT, cwd=location)
        self.file_stdin = open(gettempdir()+'/vido.txt', 'r')
        self.current_url[0] = "Processing" ; self.current_url[2] = "In progress"
        self.timer = GObject.timeout_add(1000, self.__get_status__)

    def btnSave_clicked(self, widget, data=None):
        self.__save_preferences__()

    def folderDownload_changed(self,widget):
        self.folderDownload.set_current_folder(self.folderDownload.get_filename())

    def __init_ui__(self):
        # initialise format combo box
        self.vf_list = {"Best" : "best",
                        "Audio m4a": "bestaudio[ext=m4a]",
                        "Video 360p mp4": "best[height<=360][ext=mp4]",
                        "Video 720p mp4": "best[height<=720][ext=mp4]"
                    }

        store = self.cboFormat.get_model()
        for key in sorted(self.vf_list):
            store.append([key])
        self.cboFormat.set_active_id("Best")

        # set Download folder to home
        self.folderDownload.set_current_folder(os.path.expanduser('~'))

    def __reset__(self, url_status, status_msg=None):
        try:
            if url_status=="Done":
                self.proc=None
            elif self.proc.poll()==None:
                self.proc.terminate()
            GObject.source_remove(self.timer)
            if self.current_url:
                self.current_url[0] = url_status
                if status_msg:
                    self.current_url[2] = status_msg
                self.__save_url_list__()
                self.current_url = None
            self.btnDownload.set_sensitive(True)
            self.btnClear.set_sensitive(True)
            self.listUrl.set_reorderable(True)
            self.statusbar.push(self.status_context_id,"")
            self.progress.set_text("Speed: --  ETA: --")
            self.progressbar.set_fraction(0)
        except:
            pass

    def __load_preferences__(self):
        if os.path.isfile(self.pref_file):
            preffile = open(self.pref_file, 'r')
            prefs = preffile.readline().strip().split('|')
            if len(prefs)==5:
                self.folderDownload.set_current_folder(prefs[0])
                if (prefs[1] in  self.vf_list.keys()): self.cboFormat.set_active_id(prefs[1])
                else: self.cboFormat.get_child().set_text(prefs[1])
                self.txtProxy.set_text(prefs[2])
                self.txtProxyUser.set_text(prefs[3])
                self.txtProxyPass.set_text(prefs[4])
            preffile.close()

    def __save_preferences__(self):
        line = self.folderDownload.get_current_folder()+"|"+ str(self.cboFormat.get_child().get_text())+"|"+ \
                self.txtProxy.get_text().strip()+"|"+self.txtProxyUser.get_text().strip()+"|" + \
                self.txtProxyPass.get_text().strip()
        preffile = open(self.pref_file, 'w')
        preffile.write(line)
        preffile.close()

    def __load_url_list__(self):
        if os.path.isfile(self.url_file):
            with open(self.url_file,"r") as urlfile:
                for urls in urlfile:
                    status, url, *msg = urls.strip('\n').split(',')
                    self.listUrl.get_model().append([status,url,", ".join(msg)])

    def __save_url_list__(self):
        with open(self.url_file,"w") as urlfile:
            urls = self.builder.get_object("listUrl").get_model()
            for row in urls:
                urlfile.write("%s,%s,%s\n"%(row[0],row[1],row[2]))

    def __download_params__(self):
        params=[]
        #format
        format_str = "--format=%s"%(self.vf_list[self.cboFormat.get_active_id()]
            if self.cboFormat.get_active_id() else self.cboFormat.get_child().get_text())
        params.append(format_str)
        #proxy
        if self.txtProxyUser.get_text().strip()!="":
            proxy_url=self.txtProxy.get_text().split('//')
            proxy_url=proxy_url[0]+"//"+self.txtProxyUser.get_text().strip()+":"+self.txtProxyPass.get_text()+"@"+proxy_url[1]
        else:
            proxy_url=self.txtProxy.get_text();
        params+=["--proxy",proxy_url]
        #user/pass
        return params

    def __get_status__(self):
        msg = self.file_stdin.readline().strip()
        if (msg!=""):
            msg_part = msg.split()
            if (msg_part[0]=="ERROR:"):
                self.__reset__("Error"," ".join(msg_part[1:]))
                self.btnDownload_clicked(None) #invoke next queued url download
            elif (msg_part[0]=="[download]"):
                if msg_part[1]=="Destination:":
                    self.current_url[2]=" ".join(msg_part[2:]) # set file name as message
                elif len(msg_part)>=6:
                    if msg_part[-6]=="of" and msg_part[-4]=="at" and msg_part[-2]=="ETA":
                        self.progress.set_text(("Speed: %s ETA: %s")%(msg_part[5],msg_part[7]))
                        self.progressbar.set_fraction(float(msg_part[-7][:-1])/100)
                    elif msg_part[-4]=="of" and msg_part[-2]=="in": #100% of SIZE in TIME
                        self.__reset__("Done")
                        self.btnDownload_clicked(None) #invoke next queued url download
                    elif " ".join(msg_part[-4:])=="has already been downloaded":
                        self.__reset__("Done"," ".join(msg_part[1:-4])) #send downloaded filename
                        self.btnDownload_clicked(None) #invoke next queued url download
            else:
                self.statusbar.push(self.status_context_id,msg)
        #If process has exited report termination
        elif self.proc.poll() != None:
            self.__reset__("Queued", 'Unexpected Termination')
            self.btnDownload_clicked(None) #invoke re-download
        return True


    def __next_url__(self):
        for row in self.listUrl.get_model():
            if row[0] == 'Queued':
                return row
                break
        return None

    def status_clicked(self, widget):
        ## on clicking the status icon show window and set default tab to downloads ##
        if self.iconified:
            self.winmain.show()
            self.winmain.deiconify()
            #self.builder.get_object("notebook").set_current_page(0)
            self.iconified = False
        else:
            self.winmain.hide()
            self.iconified=True

    def init_droparea(self):
        ###initialize drop window and connect to accept dropped urls###
        self.w = Gtk.Window()
        self.w.set_skip_taskbar_hint(True)
        self.box = Gtk.EventBox ()
        self.w.add (self.box)
        drop_image = Gtk.Image()
        drop_image.set_from_file('vido.svg')
        self.box.add(drop_image)
        self.w.set_size_request(30,30)
        self.w.set_decorated(False)
        self.w.set_deletable(False)
        self.w.set_keep_above(True)
        self.w.stick()
        self.w.drag_dest_set(Gtk.DestDefaults.ALL,None,Gdk.DragAction.COPY)
        self.w.drag_dest_add_text_targets()
        self.w.connect('drag_data_received', self.linkdrop)
        self.box.connect('button_press_event',self.drag_window)
        ## On closing the drop window explicitly hide window ##
        self.w.connect('delete_event',self.btnDrop_clicked)

    def drag_window(self,widget,event):
        ## move droparea on dragging ##
        self.w.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time);
        return True

    def linkdrop(self,widget, context, x, y, data, info, time):
        ## get url and queue it ##
        url = data.get_text().strip()
        if url!= "":
            self.builder.get_object("listUrl").get_model().append(["Queued",url,''])
        self.__save_url_list__()
        context.finish(True, False, time)
        return True

if __name__ =='__main__':
    #replace if vidoMain is not the main class
    vidoMain()
    Gtk.main()
