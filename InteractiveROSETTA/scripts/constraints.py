import wx
import wx.grid
import wx.lib.scrolledpanel
import os
import os.path
import time
import platform
import multiprocessing
import Bio.PDB
import webbrowser
from threading import Thread
from tools import *

class ConstraintPanel(wx.lib.scrolledpanel.ScrolledPanel):
    '''A panel allowing for the selection of constraints.  Easily added into any
    pre-existing module.  Note: Doesn't need to be a ScrolledPanel because its
    parent will be a ScrolledPanel'''

    def __init__(self, parent,minPanel):
      # print 'creating constraint panel'
      wx.lib.scrolledpanel.ScrolledPanel.__init__(self,parent,-1,size=(800,500))
      self.parent = parent
      self.minPanel = minPanel
      # print 'Panel initialized'
      #sizer
      sizer = wx.GridBagSizer(10,10)
      self.SetSizer(sizer)

      #Add constraint button
      self.ConstraintBtn = wx.Button(self,-1,label="Add Constraint")
      self.ConstraintBtn.SetForegroundColour("#000000")
      self.ConstraintBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.ITALIC,wx.BOLD))
      self.ConstraintBtn.Bind(wx.EVT_BUTTON,self.addConstraint)
      self.ConstraintBtn.SetToolTipString("Add a new constraint to the simulation")
      self.Sizer.Add(self.ConstraintBtn,(0,0),(1,1))
      #self.Layout()
      # print 'constraint button done'
      # print 'load button'
      self.Cancelables = []
      self.CurrentConstraint = {}
    #   self.ConstraintSet = self.minPanel.ConstraintSet

      #Remove Constraint Button
      self.DelBtn = wx.Button(self,-1,label="Delete Constraint")
      self.DelBtn.SetForegroundColour("#000000")
      self.DelBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.ITALIC,wx.BOLD))
      self.DelBtn.Bind(wx.EVT_BUTTON,self.DelConstraint)
      self.Sizer.Add(self.DelBtn,(0,1),(1,1))
      #Clear Constraints Button
      self.ClearBtn = wx.Button(self,-1,label="Clear Constraints")
      self.ClearBtn.SetForegroundColour("#000000")
      self.ClearBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.ITALIC,wx.BOLD))
      self.ClearBtn.Bind(wx.EVT_BUTTON,self.ClearConstraints)
      self.Sizer.Add(self.ClearBtn,(0,2),(1,1))
      '''
      #Help Button
        if platform.system() == 'Darwin':
            self.HelpBtn = wx.BitmapButton(self,id=-1,bitmap=wx.Image(self.parent.parent.scriptdir+'/images/osx/HelpBtn.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap(),pos=(295,10),size=(25,25))
        else:
            self.HelpBtn = wx.Button(self, id=-1,label='?',pos=(295,10),size=(25,25))
            self.HelpBtn.SetForegroundColour("#0000FF")
            self.HelpBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.BOLD))
        self.HelpBtn.Bind(wx.EVT_BUTTON,self.showHelp)
        self.HelpBtn.SetToolTipString("Display the help file for this window")
        logInfo('408: Help button set')
      '''
      #Help Button
      self.HelpBtn = wx.Button(self, id=-1,label='?',size=(25,25))
      self.HelpBtn.SetForegroundColour("#0000FF")
      self.HelpBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.BOLD))
      self.HelpBtn.Bind(wx.EVT_BUTTON,self.showHelp)
      self.HelpBtn.SetToolTipString("Display the help file for this window")
      logInfo('408: Help button set')
      self.Sizer.Add(self.HelpBtn,(0,3),(1,1))

      #Constraints Grid
      # print 'starting constraints grid'
      self.constraintsGrid = wx.grid.Grid(self)
      self.constraintsGrid.CreateGrid(0,1)
      self.constraintsGrid.SetLabelFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
      self.constraintsGrid.SetColLabelValue(0,"Constraint String")
      self.constraintsGrid.SetRowLabelSize(80)
      self.constraintsGrid.SetColSize(0,400)
      self.constraintsGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.gridClick)
      self.selectdr = -1
      self.Sizer.Add(self.constraintsGrid,(6,0),(10,6),wx.EXPAND)
      self.Layout()
      # print 'grid created'

    #   print self.minPanel.ConstraintSet
      for [pdb,pindx,cst] in self.minPanel.ConstraintSet:
           self.addToGrid("%s: %s"%(pdb,cst))
      #Scrolling
      self.SetupScrolling()
      # print 'scrolling'


    def showHelp(self, event):
        '''Open the help page'''
        if platform.system() == 'Darwin':
            try:
                browser = webbrowser.get('Safari')
            except Exception as e:
                print 'Could not load Safari!  The help files are located at %s/help'%(self.parent.parent.scriptdir)
                print e.message
                import traceback, sys; traceback.print_tb(sys.exc_info()[2])
                return
            browser.open(self.minPanel.parent.parent.scriptdir+'/help/constraints.html')
        else:
            webbrowser.open(self.minPanel.parent.parent.scriptdir+'/help/constraints.html')

    def DelConstraint(self,event):
      logInfo("Delete Constraint button pushed!")
      row = self.selectdr
      # print row
    #   self.ConstraintSet.pop(row)
      self.minPanel.ConstraintSet.pop(row)
      self.constraintsGrid.DeleteRows(row,1)
      # print self.ConstraintSet

    def ClearConstraints(self,event):
      logInfo("Clear Constraints button pushed!")
    #   self.ConstraintSet = []
      self.minPanel.ConstraintSet = []
      self.constraintsGrid.DeleteRows(0,self.constraintsGrid.NumberRows)

    def setSeqWin(self,seqWin):
      self.seqWin = seqWin

    def setPyMOL(self, pymol):
      self.pymol = pymol
      self.cmd = pymol.cmd
      self.stored = pymol.stored

    def setSelectWin(self, selectWin):
      self.selectWin = selectWin
      self.selectWin.setProtPanel(self)

    #Event Listeners

    def addConstraint(self,event):
      '''Adds a new constraint to the set of constraints'''
      logInfo('Add Constraint button clicked!')
      constraintTypes = ['Constraint Type','AtomPair','Angle','Dihedral','CoordinateConstraint']
      self.constraintTypeMenu = wx.ComboBox(self,choices=constraintTypes,style=wx.CB_READONLY)
      self.constraintTypeMenu.SetSelection(0)
#      self.constraintTypeMenu.Bind(wx.EVT_COMBOBOX,self.setConstraintType)
      self.Sizer.Add(self.constraintTypeMenu,(1,0),(1,1))
      self.Cancelables.append(self.constraintTypeMenu)
      #PDB MENU
      pdbs = ['Choose PDB']
      # print pdbs
      for [indx, r, seqpos, poseindx, chainoffset, minType,r_indx] in self.minPanel.minmap:
        # print "poseindx",poseindx
        if len(pdbs) == 0:
          # print 'appending',poseindx
          pdbs.append(poseindx)
        isThere = False
        for i in range(0,len(pdbs)):
          if poseindx == pdbs[i]:
            # print("%i = %i"%(poseindx,pdbs[i]))
            isThere = True
            break
        if not isThere:
          # print 'appending',poseindx
          pdbs.append(poseindx)
      # print pdbs
      for i in range(1,len(pdbs)):
        pdbs[i] = str(self.seqWin.poses[pdbs[i]].get_id())
        # print pdbs[i]
      # print pdbs
      self.PdbMenu = wx.ComboBox(self,choices=pdbs,style=wx.CB_READONLY)
      self.PdbMenu.SetSelection(0)
#      self.PdbMenu.Bind(wx.EVT_COMBOBOX,self.setConstraintPDB)
      self.Cancelables.append(self.PdbMenu)
      self.Sizer.Add(self.PdbMenu,(1,1),(1,1))
      self.Layout()


      #Constraint Function
      self.FuncMenu = wx.ComboBox(self,-1,choices=["Select Constraint Function","Harmonic","Circular Harmonic"],style=wx.CB_READONLY)
      self.FuncMenu.SetSelection(0)
#      self.FuncMenu.Bind(wx.EVT_COMBOBOX,self.setFunction)
      self.Sizer.Add(self.FuncMenu,(1,2),(1,1))
      self.Layout()

      self.Cancelables.append(self.FuncMenu)

      #Next Button
      self.NextBtn = wx.Button(self,-1,label='Confirm')
      self.NextBtn.Bind(wx.EVT_BUTTON,self.Next)
      self.Sizer.Add(self.NextBtn,(1,3),(1,1))
      self.Layout()

      self.Cancelables.append(self.NextBtn)
      # print 'pdbmenu'
      #self.Layout()

      #Cancel Button
      self.CancelBtn = wx.Button(self,-1,label='Cancel')
      self.CancelBtn.Bind(wx.EVT_BUTTON,self.cancel)
      self.Sizer.Add(self.CancelBtn,(5,2),(1,1))
      self.Cancelables.append(self.CancelBtn)
      self.Layout()

      self.SetupScrolling()

    def Next(self,event):
      '''generate remaining menu based on initial choices'''
      self.CurrentConstraint['PDB'] = self.PdbMenu.GetStringSelection()
      self.CurrentConstraint['ConstraintType'] = self.constraintTypeMenu.GetStringSelection()
      self.CurrentConstraint['FuncType'] = self.FuncMenu.GetStringSelection()
      if self.CurrentConstraint['PDB'] == 'Choose PDB' or self.CurrentConstraint['ConstraintType'] == 'Constraint Type' or self.CurrentConstraint['FuncType']=='Select Constraint Function':
        self.CurrentConstraint = {}
        event.skip()
      else:
        for item in [self.PdbMenu,self.constraintTypeMenu,self.FuncMenu,self.NextBtn]:
          item.Show(False)
          item.Destroy()
        constraintlbl = "Constraint Type: %s"%(self.CurrentConstraint['ConstraintType'])
        Pdblbl = "PDB: %s"%(self.CurrentConstraint['PDB'])
        funclbl = "Constraint Function: %s"%(self.CurrentConstraint["FuncType"])
        self.ConstraintTxt = wx.StaticText(self,-1,label=constraintlbl)
        self.PdbTxt = wx.StaticText(self,-1,label=Pdblbl)
        self.FuncTxt = wx.StaticText(self,-1,label=funclbl)
        self.Sizer.Add(self.ConstraintTxt,(1,0),(1,1))
        self.Sizer.Add(self.PdbTxt,(1,1),(1,1))
        self.Sizer.Add(self.FuncTxt,(1,2),(1,1))
        self.Layout()

        self.Cancelables = [self.ConstraintTxt,self.PdbTxt,self.FuncTxt,self.CancelBtn]

        #set poseindx
        for [indx, r, seqpos, poseindx, chainoffset, minType,r_indx] in self.minPanel.minmap:
          if str(self.seqWin.poses[poseindx].get_id())==self.CurrentConstraint['PDB']:
            self.CurrentConstraint['poseindx']=poseindx
            break

        #check which constraint method was selected and behave accordingly
        method = self.CurrentConstraint['ConstraintType']
        #AtomPair
        if method not in ['AtomPair','Angle','Dihedral','CoordinateConstraint']:
          self.cancel()
          return
        else:
          #Residue 1
          res1items = ['Select Residue 1']+self.getResidues()
          self.Residue1Menu = wx.ComboBox(self,-1,choices=res1items,style=wx.CB_READONLY)
          self.Residue1Menu.Bind(wx.EVT_COMBOBOX,self.setAtom1Items)
          self.Residue1Menu.SetSelection(0)
          self.Sizer.Add(self.Residue1Menu,(2,0),(1,1))
          self.Layout()

          self.Cancelables.append(self.Residue1Menu)
          #Atom 1
          self.Atom1Menu = wx.ComboBox(self,-1,choices=['Select Atom 1'],style=wx.CB_READONLY)
          self.Atom1Menu.SetSelection(0)
          self.Sizer.Add(self.Atom1Menu,(2,1),(1,1))
          self.Layout()

          self.Cancelables.append(self.Atom1Menu)
          #Residue 2
          res2items = ['Select Residue 2']+self.getResidues()
          self.Residue2Menu = wx.ComboBox(self,-1,choices=res2items,style=wx.CB_READONLY)
          self.Residue2Menu.Bind(wx.EVT_COMBOBOX,self.setAtom2Items)
          self.Residue2Menu.SetSelection(0)
          self.Sizer.Add(self.Residue2Menu,(2,2),(1,1))
          self.Layout()

          self.Cancelables.append(self.Residue2Menu)
          #Atom 2
          self.Atom2Menu = wx.ComboBox(self,-1,choices=['Select Atom 2'],style=wx.CB_READONLY)
          self.Atom2Menu.SetSelection(0)
          self.Sizer.Add(self.Atom2Menu,(2,3),(1,1))
          self.Layout()

          self.Cancelables.append(self.Atom2Menu)

          #Angle or Dihdedral
          if method in ['Angle','Dihedral']:
            self.Residue3Menu = wx.ComboBox(self,-1,choices=['Select Residue 3']+self.getResidues(),style=wx.CB_READONLY)
            self.Residue3Menu.SetSelection(0)
            self.Sizer.Add(self.Residue3Menu,(3,0),(1,1))
            self.Layout()

            self.Cancelables.append(self.Residue3Menu)
            self.Residue3Menu.Bind(wx.EVT_COMBOBOX,self.setAtom3Items)
            #Atom 3
            self.Atom3Menu = wx.ComboBox(self,-1,choices=['Select Atom 3'],style=wx.CB_READONLY)
            self.Atom3Menu.SetSelection(0)
            self.Sizer.Add(self.Atom3Menu,(3,1),(1,1))
            self.Layout()

            self.Cancelables.append(self.Atom3Menu)

          #Dihedral only
          if method == 'Dihedral':
            #Residue 4
            self.Residue4Menu = wx.ComboBox(self,-1,choices=['Select Residue 4']+self.getResidues(),style=wx.CB_READONLY)
            self.Residue4Menu.SetSelection(0)
            self.Sizer.Add(self.Residue4Menu,(3,2),(1,1))
            self.Layout()

            self.Cancelables.append(self.Residue4Menu)
            self.Residue4Menu.Bind(wx.EVT_COMBOBOX,self.setAtom4Items)
            #Atom 4
            self.Atom4Menu = wx.ComboBox(self,-1,choices=['Select Atom 4'],style=wx.CB_READONLY)
            self.Atom4Menu.SetSelection(0)
            self.Sizer.Add(self.Atom4Menu,(3,3),(1,1))
            self.Layout()

            self.Cancelables.append(self.Atom4Menu)

          #Coordinate only
          #Use wx.StaticText labels and wx.TextCtrl for entering text
          if method == 'CoordinateConstraint':
            #X
            self.xText = wx.StaticText(self,-1,'X Coordinate')
            self.xEntry = wx.TextCtrl(self,-1,"")
            #Y
            self.yText = wx.StaticText(self,-1,'Y Coordinate')
            self.yEntry = wx.TextCtrl(self,-1,"")
            #Z
            self.zText = wx.StaticText(self,-1,'Z Coordinate')
            self.zEntry = wx.TextCtrl(self,-1,"")
            #Add entries to sizer
            self.Sizer.Add(self.xText,(3,0),(1,1))
            self.Sizer.Add(self.xEntry,(3,1),(1,1))
            self.Sizer.Add(self.yText,(3,2),(1,1))
            self.Sizer.Add(self.yEntry,(3,3),(1,1))
            self.Sizer.Add(self.zText,(3,4),(1,1))
            self.Sizer.Add(self.zEntry,(3,5),(1,1))
            self.Layout()

            self.Cancelables+=[self.xText,self.xEntry,self.yText,self.yEntry,self.zText,self.zEntry]
        #Function type stuff
        if self.CurrentConstraint['FuncType'] in ['Harmonic','Circular Harmonic']:
          if method in ['AtomPair','CoordinateConstraint']:
            self.x0Text = wx.StaticText(self,-1,"Cut-off Distance")
          else:
            self.x0Text = wx.StaticText(self,-1,"Cut-off Angle")
          self.x0Entry = wx.TextCtrl(self,-1,"")
          self.sdText = wx.StaticText(self,-1,"Standard Deviation")
          self.sdEntry = wx.TextCtrl(self,-1,"")
          self.Cancelables += [self.x0Text,self.x0Entry,self.sdText,self.sdEntry]
        self.FinalizeBtn = wx.Button(self,-1,label="Finalize!")
        self.FinalizeBtn.SetForegroundColour("#000000")
        self.FinalizeBtn.SetFont(wx.Font(10,wx.DEFAULT,wx.ITALIC,wx.BOLD))
        self.FinalizeBtn.Bind(wx.EVT_BUTTON,self.FinalizeConstraint)
        self.Sizer.Add(self.x0Text,(4,1),(1,1))
        self.Sizer.Add(self.x0Entry,(4,2),(1,1))
        self.Sizer.Add(self.sdText,(4,3),(1,1))
        self.Sizer.Add(self.sdEntry,(4,4),(1,1))
        self.Sizer.Add(self.FinalizeBtn,(5,0),(1,1))
        self.Layout()

        self.Cancelables.append(self.FinalizeBtn)
        self.SetupScrolling()


    def cancel(self,event=None):
      logInfo('Cancel Button Pressed!')
      # print('Cancel Button Pressed!')
      for item in self.Cancelables:
        item.Show(False)
        item.Destroy()
      self.Cancelables = []
      self.CurrentConstraint = {}
      self.Layout()

      self.SetupScrolling()


    def getResidues(self):
      minmap = self.minPanel.minmap
      residues = []
      poseindx = self.CurrentConstraint['poseindx']
      for [indx, r, seqpos, p, chainoffset, minType,r_indx] in minmap:
        if p == poseindx:
          # print indx, r, seqpos, p, chainoffset, r_indx
          chain = self.seqWin.IDs[r][len(self.seqWin.IDs[r])-1]
          if chain == '_':
            chain = ' '
          # print self.seqWin.poses[poseindx][0]
          # print chain
          chain_structure = self.seqWin.poses[poseindx][0][chain]
          # print chain_structure.get_id()
          residue = str(r_indx)+":"
          residue += chain_structure[int(seqpos)].resname+":"
          # print residue
          #Only considering standard amino acids for the moment
          if residue.split(":")[1] in "ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR":
            residue += str(seqpos)+":"
            residue += chain
            # print residue
            residues.append(residue)
      return residues

    def setConstraintPDB(self,event):
      logInfo("constraint PDB set!")
      self.CurrentConstraint['PDB']=self.PdbMenu.GetStringSelection()
      for i in range(0,len(self.seqWin.poses)):
        if str(self.seqWin.poses[i].get_id()) == self.CurrentConstraint['PDB']:
          self.CurrentConstraint['poseindx'] = i
          break
      items = ['Select residue 1']
      items += self.getResidues()
      # print items
      self.Residue1Menu = wx.ComboBox(self,choices=items,style=wx.CB_READONLY)
      self.Residue1Menu.Bind(wx.EVT_COMBOBOX,self.setAtom1Items)
      self.Cancelables.append(self.Residue1Menu)
      self.Sizer.Add(self.Residue1Menu,(2,0),(1,1))
      self.Layout()
      atoms = ['Select Atom 1']
      self.Atom1Menu = wx.ComboBox(self,choices=atoms,style=wx.CB_READONLY)
      self.Atom1Menu.Bind(wx.EVT_COMBOBOX,self.ConstraintSpecifics)
      self.Cancelables.append(self.Atom1Menu)
      self.Sizer.Add(self.Atom1Menu,(2,1),(1,1))
      self.Layout()

    def setAtom1Items(self,event):
      residue = self.Residue1Menu.GetStringSelection()
      [r_indx,resname,seqpos,chain] = residue.split(":")
      self.CurrentConstraint['Atom1_ResNum']=r_indx
      atoms = ["Select Atom 1"]+self.getAtoms(residue)
      # print atoms
      self.Atom1Menu.Clear()
      self.Atom1Menu.AppendItems(atoms)
      self.Atom1Menu.SetSelection(0)

    def getAtoms(self,residue):
      results = []
      poseindx = self.CurrentConstraint['poseindx']
      [r_indx,resname,seqpos,chain] = residue.split(":")
      for atom in self.seqWin.poses[poseindx][0][chain][int(seqpos)]:
        # print atom
        results.append(atom.get_fullname())
      return results

    def setAtom2Items(self,event):
      residue = self.Residue2Menu.GetStringSelection()
      [r_indx,resname,seqpos,chain] = residue.split(":")
      self.CurrentConstraint['Atom2_ResNum']=r_indx
      atoms = ["Select Atom 2"]+self.getAtoms(residue)
      # print atoms
      self.Atom2Menu.Clear()
      self.Atom2Menu.AppendItems(atoms)
      self.Atom2Menu.SetSelection(0)
    def setAtom3Items(self,event):
      residue = self.Residue3Menu.GetStringSelection()
      [r_indx,resname,seqpos,chain] = residue.split(":")
      self.CurrentConstraint['Atom3_ResNum']=r_indx
      atoms = ["Select Atom 3"]+self.getAtoms(residue)
      # print atoms
      self.Atom3Menu.Clear()
      self.Atom3Menu.AppendItems(atoms)
      self.Atom3Menu.SetSelection(0)
    def setAtom4Items(self,event):
      residue = self.Residue4Menu.GetStringSelection()
      [r_indx,resname,seqpos,chain] = residue.split(":")
      self.CurrentConstraint['Atom4_ResNum']=r_indx
      atoms = ["Select Atom 4"]+self.getAtoms(residue)
      # print atoms
      self.Atom4Menu.Clear()
      self.Atom4Menu.AppendItems(atoms)
      self.Atom4Menu.SetSelection(0)



    def FinalizeConstraint(self,event):
      pdb = self.CurrentConstraint["PDB"]
      method = self.CurrentConstraint['ConstraintType']
      constraintString = method+' '
      #Atom1 and Atom2
      constraintString += "%s %s %s %s"%(self.Atom1Menu.GetStringSelection().strip(),self.CurrentConstraint['Atom1_ResNum'].strip(),self.Atom2Menu.GetStringSelection().strip(),self.CurrentConstraint['Atom2_ResNum'].strip())
      #Atom3
      if method in ['Angle','Dihedral']:
        constraintString += " %s %s"%(self.Atom3Menu.GetStringSelection().strip(),self.CurrentConstraint['Atom3_ResNum'].strip())
      #Atom4
      if method == 'Dihedral':
        constraintString += " %s %s"%(self.Atom4Menu.GetStringSelection().strip(),self.CurrentConstraint['Atom4_ResNum'].strip())
      #CoordinateConstraint
      if method == 'CoordinateConstraint':
        #self.xEntry.SelectAll()
        #self.yEntry.SelectAll()
        #self.zEntry.SelectAll()
        constraintString += " %s %s %s"%(self.xEntry.GetValue().strip(),self.yEntry.GetValue().strip(),self.zEntry.GetValue().strip())

      #Function Types
      functions = {'Harmonic':"HARMONIC",'Circular Harmonic':'CIRCULARHARMONIC'}
      if self.CurrentConstraint['FuncType'] in ['Harmonic','Circular Harmonic']:
        #self.x0Entry.SelectAll()
        #self.sdEntry.SelectAll()
        # print 'self.x0Entry: ',self.x0Entry.GetValue().strip()," unstripped: ",self.x0Entry.GetValue()
        # print 'self.sdEntry: ',self.sdEntry.GetValue().strip()
        constraintString += ' %s %s %s'%(functions[self.CurrentConstraint['FuncType']].strip(),self.x0Entry.GetValue().strip(),self.sdEntry.GetValue().strip())
      # print constraintString
      logInfo(constraintString)
    #   self.ConstraintSet.append([self.CurrentConstraint['PDB'],self.CurrentConstraint['poseindx'],constraintString])
      self.minPanel.ConstraintSet.append([self.CurrentConstraint['PDB'],self.CurrentConstraint['poseindx'],constraintString])
      self.addToGrid("%s: %s"%(self.CurrentConstraint['PDB'],constraintString))
      self.cancel()

    def addToGrid(self,constraintString):
      logInfo("adding string to grid: %s"%(constraintString))
      row = self.constraintsGrid.NumberRows
      self.constraintsGrid.AppendRows(1)
      self.constraintsGrid.SetCellValue(row,0,constraintString)


    def gridClick(self,event):
      logInfo('Constraints Grid Clicked!')
      self.selectdr = event.GetRow()
      # print self.selectdr
