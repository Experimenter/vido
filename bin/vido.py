import gi, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from subprocess import *
from tempfile import gettempdir

class vidoMain:

    def __init__( self ):
    
        self.builder = Gtk.Builder()
        self.builder.add_from_file("../share/vido/vido.glade")
        
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
        }
        self.builder.connect_signals(dic)
        
        self.statusicon = Gtk.StatusIcon()
        self.statusicon.set_from_file('../share/vido/vido.svg')
        
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
        pass
        
    def btnCancel_clicked(self, widget, data=None):
        self.__reset__("Queued","User Abort")
        
    def btnDownload_clicked(self, widget, data=None):
        self.current_url = self.__next_url__()
        if not self.current_url: return
        self.btnDownload.set_sensitive(False)
        self.btnClear.set_sensitive(False)
        self.listUrl.set_reorderable(False)
        location = self.folderDownload.get_current_folder()
        vido_cmd = ["youtube-dl", "-t", "-c"]+self.__download_params__()
        vido_cmd.append(self.current_url[1])
        print (vido_cmd) #print parameters for inspection
        self.file_stdout = open(gettempdir()+'/vido.txt', 'w')
        self.proc = Popen(vido_cmd,  stdout=self.file_stdout, stderr=STDOUT, cwd=location)
        self.file_stdin = open(gettempdir()+'/vido.txt', 'r')
        self.current_url[0] = "Processing" ; self.current_url[2] = "In progress"
        self.timer = GObject.timeout_add(1000, self.__get_status__)
        
    def btnSave_clicked(self, widget, data=None):
        self.__save_preferences__()
        
    def __init_ui__(self):
        # initialise format combo box
        vf_list = { "Audio m4a":"--format=140",
                    "Mobile"  : "--format=17",
                    "Hi-def"  : "--format=35",
                    "flv 240p": "--format=5",
                    "flv 360p": "--format=34",
                    "flv 480p": "--format=35",
                    "mp4 360p": "--format=18",
                    "mp4 720p": "--format=22",
                    "mp4 720p": "--format=hd720",
                    "mp4 480p": "--format=hq"
                  }

        store = self.cboFormat.get_model()
        store.append(["Default","--format=best"])
        for key in sorted(vf_list):
            store.append([key,vf_list[key]])
        self.cboFormat.set_active(0)
        
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
                self.cboFormat.set_active(int(prefs[1]))
                self.txtProxy.set_text(prefs[2])
                self.txtProxyUser.set_text(prefs[3])
                self.txtProxyPass.set_text(prefs[4])
            preffile.close()
    
    def __save_preferences__(self):
        line = self.folderDownload.get_current_folder()+"|"+ str(self.cboFormat.get_active())+"|"+ \
                self.txtProxy.get_text().strip()+"|"+self.txtProxyUser.get_text().strip()+"|" + \
                self.txtProxyPass.get_text().strip()
        preffile = open(self.pref_file, 'w')
        preffile.write(line)
        preffile.close()
        
    def __load_url_list__(self):
        if os.path.isfile(self.url_file):
            urlfile = open(self.url_file,"r")
            for urls in urlfile:
                try:
                    status, url, msg = urls.strip('\n').split(',')
                    self.listUrl.get_model().append([status,url,msg])
                except:
                    pass
            urlfile.close()
        
    def __save_url_list__(self):
        urlfile = open(self.url_file,"w")
        urls = self.builder.get_object("listUrl").get_model()
        for row in urls:
            urlfile.write("%s,%s,%s\n"%(row[0],row[1],row[2]))
        urlfile.close()
        
    def __download_params__(self):
        params=[]
        #format
        params.append(self.cboFormat.get_model()[self.cboFormat.get_active()][1])
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
                    elif msg_part[-4]=="of" and msg_part[-2]=="in":
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

if __name__ =='__main__':
    #replace if vidoMain is not the main class
    vidoMain()
    Gtk.main()
