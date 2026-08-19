// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import Layout from 'antd/lib/layout';

import { ActiveControl, CombinedState, Rotation } from 'reducers';
import GlobalHotKeys, { KeyMap } from 'utils/mousetrap-react';
import { Canvas, CanvasMode } from 'cvat-canvas-wrapper';
import { ShortcutScope } from 'utils/enums';
import { registerComponentShortcuts } from 'actions/shortcuts-actions';
import { subKeyMap } from 'utils/component-subkeymap';
import CursorControl from './cursor-control';
import MoveControl from './move-control';
import FitControl from './fit-control';
import ResizeControl from './resize-control';
import DrawRectangleControl from './draw-rectangle-control';

type Label = CombinedState['annotation']['job']['labels'][0];

interface Props {
    canvasInstance: Canvas;
    activeControl: ActiveControl;
    keyMap: KeyMap;
    normalizedKeyMap: Record<string, string>;
    labels: Label[];
    frameData: any;
    updateActiveControl(activeControl: ActiveControl): void;
    rotateFrame(rotation: Rotation): void;
    repeatDrawShape(): void;
    pasteShape(): void;
    resetGroup(): void;
    redrawShape(): void;
}

const componentShortcuts = {
    PASTE_SHAPE: {
        name: '粘贴标注框',
        description: '粘贴已复制的标注框',
        sequences: ['ctrl+v'],
        scope: ShortcutScope.OBJECTS_SIDEBAR,
    },
    SWITCH_DRAW_MODE_STANDARD_CONTROLS: {
        name: '重复绘制矩形框',
        description: '使用上次的类别继续绘制矩形框',
        sequences: ['n'],
        scope: ShortcutScope.STANDARD_WORKSPACE_CONTROLS,
    },
    SWITCH_REDRAW_MODE_STANDARD_CONTROLS: {
        name: '重新绘制矩形框',
        description: '删除当前矩形框并重新绘制',
        sequences: ['shift+n'],
        scope: ShortcutScope.STANDARD_WORKSPACE_CONTROLS,
    },
};

registerComponentShortcuts(componentShortcuts);

export default function ControlsSideBarComponent(props: Props): JSX.Element {
    const {
        activeControl, canvasInstance, normalizedKeyMap, keyMap, labels,
        repeatDrawShape, pasteShape, redrawShape, frameData,
    } = props;
    const controlsDisabled = !labels.length || frameData.deleted;

    const handleDrawMode = (event: KeyboardEvent | undefined, redraw: boolean): void => {
        event?.preventDefault();
        const drawing = activeControl === ActiveControl.DRAW_RECTANGLE;
        if (drawing) {
            canvasInstance.draw({ enabled: false });
        } else if (canvasInstance.mode() === CanvasMode.EDIT) {
            canvasInstance.edit({ enabled: false });
        } else {
            canvasInstance.cancel();
            if (redraw) redrawShape();
            else repeatDrawShape();
        }
    };

    const handlers: Record<keyof typeof componentShortcuts, (event?: KeyboardEvent) => void> = {
        PASTE_SHAPE: (event) => {
            event?.preventDefault();
            canvasInstance.cancel();
            pasteShape();
        },
        SWITCH_DRAW_MODE_STANDARD_CONTROLS: (event) => handleDrawMode(event, false),
        SWITCH_REDRAW_MODE_STANDARD_CONTROLS: (event) => handleDrawMode(event, true),
    };

    return (
        <Layout.Sider className='cvat-canvas-controls-sidebar' theme='light' width={44}>
            <GlobalHotKeys
                keyMap={controlsDisabled ? {} : subKeyMap(componentShortcuts, keyMap)}
                handlers={handlers}
            />
            <CursorControl
                cursorShortkey={normalizedKeyMap.CANCEL}
                canvasInstance={canvasInstance}
                activeControl={activeControl}
            />
            <MoveControl canvasInstance={canvasInstance} activeControl={activeControl} />
            <hr />
            <FitControl canvasInstance={canvasInstance} />
            <ResizeControl canvasInstance={canvasInstance} activeControl={activeControl} />
            <hr />
            <DrawRectangleControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_RECTANGLE}
                disabled={controlsDisabled}
            />
        </Layout.Sider>
    );
}
