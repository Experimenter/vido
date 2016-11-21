import gi, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

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
        self.statusicon.set_from_file('../share/vido/ytdicon.svg')
        
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
        pass
        
    def btnDownload_clicked(self, widget, data=None):
        pass
        
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
        store.append(["Default",""])
        for key in sorted(vf_list):
            store.append([key,vf_list[key]])
        self.cboFormat.set_active(0)
        
        # set Download folder to home
        self.folderDownload.set_current_folder(os.path.expanduser('~'))
    
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
        print (self.folderDownload.get_current_folder())
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
        

if __name__ =='__main__':
    #replace if vidoMain is not the main class
    vidoMain()
    Gtk.main()
