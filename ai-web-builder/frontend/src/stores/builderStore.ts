'use client';

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ComponentElement {
  id: string;
  type: 'container' | 'text' | 'button' | 'image' | 'form' | 'card' | 'hero' | 'navigation';
  name: string;
  content: string;
  styles: {
    width?: string;
    height?: string;
    padding?: string;
    margin?: string;
    backgroundColor?: string;
    color?: string;
    fontSize?: string;
    fontWeight?: string;
    borderRadius?: string;
    border?: string;
    display?: string;
    flexDirection?: string;
    justifyContent?: string;
    alignItems?: string;
    position?: string;
    top?: string;
    left?: string;
    right?: string;
    bottom?: string;
    zIndex?: number;
    [key: string]: any;
  };
  props: {
    [key: string]: any;
  };
  children: string[];
  parentId: string | null;
  order: number;
}

export interface Template {
  id: string;
  name: string;
  category: 'landing' | 'ecommerce' | 'blog' | 'portfolio' | 'corporate' | 'startup';
  description: string;
  thumbnail: string;
  elements: ComponentElement[];
  createdAt: Date;
  updatedAt: Date;
}

interface BuilderState {
  // Canvas state
  selectedElementId: string | null;
  hoveredElementId: string | null;
  elements: ComponentElement[];
  canvasMode: 'design' | 'preview';
  zoom: number;
  
  // Template state
  currentTemplate: Template | null;
  templates: Template[];
  
  // UI state
  sidebarOpen: boolean;
  activePanel: 'components' | 'templates' | 'settings' | 'ai';
  
  // Drag and drop state
  draggedElementType: string | null;
  isDropTarget: boolean;
  
  // History for undo/redo
  history: ComponentElement[][];
  historyIndex: number;
  maxHistorySize: number;
  
  // Actions
  selectElement: (id: string | null) => void;
  hoverElement: (id: string | null) => void;
  addElement: (element: Omit<ComponentElement, 'id' | 'order'>) => void;
  updateElement: (id: string, updates: Partial<ComponentElement>) => void;
  deleteElement: (id: string) => void;
  moveElement: (id: string, newParentId: string | null, newOrder: number) => void;
  duplicateElement: (id: string) => void;
  
  // Canvas actions
  setCanvasMode: (mode: 'design' | 'preview') => void;
  setZoom: (zoom: number) => void;
  
  // Template actions
  loadTemplate: (template: Template) => void;
  saveTemplate: (name: string, category: Template['category']) => void;
  
  // UI actions
  setSidebarOpen: (open: boolean) => void;
  setActivePanel: (panel: 'components' | 'templates' | 'settings' | 'ai') => void;
  
  // Drag and drop actions
  setDraggedElementType: (type: string | null) => void;
  setIsDropTarget: (isTarget: boolean) => void;
  
  // History actions
  undo: () => void;
  redo: () => void;
  saveToHistory: () => void;
  
  // Utility actions
  clearCanvas: () => void;
  getElementById: (id: string) => ComponentElement | undefined;
  getElementChildren: (id: string) => ComponentElement[];
}

const generateId = () => Math.random().toString(36).substr(2, 9);

export const useBuilderStore = create<BuilderState>()(
  devtools(
    (set, get) => ({
      // Initial state
      selectedElementId: null,
      hoveredElementId: null,
      elements: [],
      canvasMode: 'design',
      zoom: 100,
      
      currentTemplate: null,
      templates: [],
      
      sidebarOpen: true,
      activePanel: 'components',
      
      draggedElementType: null,
      isDropTarget: false,
      
      history: [[]],
      historyIndex: 0,
      maxHistorySize: 50,
      
      // Element actions
      selectElement: (id) => set({ selectedElementId: id }),
      
      hoverElement: (id) => set({ hoveredElementId: id }),
      
      addElement: (elementData) => {
        const id = generateId();
        const order = get().elements.filter(el => el.parentId === elementData.parentId).length;
        
        const newElement: ComponentElement = {
          id,
          order,
          ...elementData,
        };
        
        set((state) => ({
          elements: [...state.elements, newElement],
          selectedElementId: id,
        }));
        
        get().saveToHistory();
      },
      
      updateElement: (id, updates) => {
        set((state) => ({
          elements: state.elements.map(el => 
            el.id === id ? { ...el, ...updates } : el
          ),
        }));
        
        get().saveToHistory();
      },
      
      deleteElement: (id) => {
        const state = get();
        const elementToDelete = state.getElementById(id);
        if (!elementToDelete) return;
        
        // Also delete all children
        const getChildrenRecursively = (parentId: string): string[] => {
          const directChildren = state.elements
            .filter(el => el.parentId === parentId)
            .map(el => el.id);
          
          const allChildren = [...directChildren];
          directChildren.forEach(childId => {
            allChildren.push(...getChildrenRecursively(childId));
          });
          
          return allChildren;
        };
        
        const allIdsToDelete = [id, ...getChildrenRecursively(id)];
        
        set((state) => ({
          elements: state.elements.filter(el => !allIdsToDelete.includes(el.id)),
          selectedElementId: state.selectedElementId === id ? null : state.selectedElementId,
        }));
        
        get().saveToHistory();
      },
      
      moveElement: (id, newParentId, newOrder) => {
        set((state) => {
          const element = state.elements.find(el => el.id === id);
          if (!element) return state;
          
          // Update the moved element
          const updatedElements = state.elements.map(el => {
            if (el.id === id) {
              return { ...el, parentId: newParentId, order: newOrder };
            }
            
            // Update order of other elements in the same container
            if (el.parentId === newParentId && el.order >= newOrder && el.id !== id) {
              return { ...el, order: el.order + 1 };
            }
            
            return el;
          });
          
          return { elements: updatedElements };
        });
        
        get().saveToHistory();
      },
      
      duplicateElement: (id) => {
        const state = get();
        const element = state.getElementById(id);
        if (!element) return;
        
        const newId = generateId();
        const duplicatedElement: ComponentElement = {
          ...element,
          id: newId,
          name: `${element.name} Copy`,
          order: element.order + 1,
        };
        
        set((state) => ({
          elements: [...state.elements, duplicatedElement],
          selectedElementId: newId,
        }));
        
        get().saveToHistory();
      },
      
      // Canvas actions
      setCanvasMode: (mode) => set({ canvasMode: mode }),
      
      setZoom: (zoom) => set({ zoom: Math.max(25, Math.min(200, zoom)) }),
      
      // Template actions
      loadTemplate: (template) => {
        set({
          currentTemplate: template,
          elements: template.elements,
          selectedElementId: null,
          hoveredElementId: null,
        });
        
        get().saveToHistory();
      },
      
      saveTemplate: (name, category) => {
        const state = get();
        const template: Template = {
          id: generateId(),
          name,
          category,
          description: `Template created on ${new Date().toLocaleDateString()}`,
          thumbnail: '', // TODO: Generate thumbnail
          elements: state.elements,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        
        set((state) => ({
          templates: [...state.templates, template],
          currentTemplate: template,
        }));
      },
      
      // UI actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      setActivePanel: (panel) => set({ activePanel: panel }),
      
      // Drag and drop actions
      setDraggedElementType: (type) => set({ draggedElementType: type }),
      
      setIsDropTarget: (isTarget) => set({ isDropTarget: isTarget }),
      
      // History actions
      undo: () => {
        const state = get();
        if (state.historyIndex > 0) {
          const newIndex = state.historyIndex - 1;
          set({
            elements: state.history[newIndex],
            historyIndex: newIndex,
            selectedElementId: null,
          });
        }
      },
      
      redo: () => {
        const state = get();
        if (state.historyIndex < state.history.length - 1) {
          const newIndex = state.historyIndex + 1;
          set({
            elements: state.history[newIndex],
            historyIndex: newIndex,
            selectedElementId: null,
          });
        }
      },
      
      saveToHistory: () => {
        const state = get();
        const newHistory = state.history.slice(0, state.historyIndex + 1);
        newHistory.push([...state.elements]);
        
        if (newHistory.length > state.maxHistorySize) {
          newHistory.shift();
        } else {
          set({ historyIndex: state.historyIndex + 1 });
        }
        
        set({ history: newHistory });
      },
      
      // Utility actions
      clearCanvas: () => {
        set({
          elements: [],
          selectedElementId: null,
          hoveredElementId: null,
          currentTemplate: null,
        });
        
        get().saveToHistory();
      },
      
      getElementById: (id) => {
        return get().elements.find(el => el.id === id);
      },
      
      getElementChildren: (id) => {
        return get().elements
          .filter(el => el.parentId === id)
          .sort((a, b) => a.order - b.order);
      },
    }),
    {
      name: 'builder-store',
    }
  )
);