// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { Col } from 'antd/lib/grid';
import Icon, { StopOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import Modal from 'antd/lib/modal';
import Button from 'antd/lib/button';
import Text from 'antd/lib/typography/Text';

import { UndoIcon, RedoIcon } from 'icons';
import { ActiveControl, ToolsBlockerState } from 'reducers';
import { registerComponentShortcuts } from 'actions/shortcuts-actions';
import AnnotationMenuComponent from 'components/annotation-page/top-bar/annotation-menu';
import CVATTooltip from 'components/common/cvat-tooltip';
import { ShortcutScope } from 'utils/enums';
import { subKeyMap } from 'utils/component-subkeymap';
import GlobalHotKeys, { KeyMap } from 'utils/mousetrap-react';
import { finishDrawAvailable } from 'utils/drawing';
import SaveAnnotationsButton from './save-annotations-button';

interface Props {
    saving: boolean;
    undoAction?: string;
    redoAction?: string;
    undoShortcut: string;
    redoShortcut: string;
    drawShortcut: string;
    switchToolsBlockerShortcut: string;
    toolsBlockerState: ToolsBlockerState;
    activeControl: ActiveControl;
    keyMap: KeyMap;
    onUndoClick(): void;
    onRedoClick(): void;
    onFinishDraw(): void;
    onSwitchToolsBlockerState(): void;
}

const componentShortcuts = {
    UNDO: {
        name: '撤销',
        description: '撤销上一次标注操作',
        sequences: ['ctrl+z'],
        scope: ShortcutScope.ANNOTATION_PAGE,
    },
    REDO: {
        name: '重做',
        description: '恢复上一次撤销的操作',
        sequences: ['ctrl+shift+z', 'ctrl+y'],
        scope: ShortcutScope.ANNOTATION_PAGE,
    },
    SWITCH_TOOLS_BLOCKER_STATE: {
        name: '暂停算法工具',
        description: '暂停交互式算法工具',
        sequences: ['tab'],
        scope: ShortcutScope.STANDARD_WORKSPACE,
    },
};

const historyActionNames: Record<string, string> = {
    'Changed label': '修改类别',
    'Changed attributes': '修改属性',
    'Changed points': '调整标注框',
    'Object rotated': '旋转标注',
    'Changed outside': '修改画面外状态',
    'Changed occluded': '修改遮挡状态',
    'Changed z-order': '修改图层顺序',
    'Changed keyframe': '修改关键帧',
    'Changed lock': '修改锁定状态',
    'Changed pinned': '修改固定状态',
    'Changed color': '修改颜色',
    'Changed hidden': '修改显示状态',
    'Changed source': '修改来源',
    'Changed audio position': '修改音频位置',
    'Merged objects': '合并标注',
    'Joined objects': '连接标注',
    'Sliced object': '切分标注',
    'Splitted track': '拆分轨迹',
    'Grouped objects': '组合标注',
    'Created objects': '创建标注框',
    'Removed object': '删除标注框',
    'Removed frame': '删除图片',
    'Restored frame': '恢复图片',
    'Commit annotations': '提交标注',
};

function localizeHistoryAction(action?: string): string {
    return action ? historyActionNames[action] || action : '';
}

registerComponentShortcuts(componentShortcuts);

function LeftGroup(props: Props): JSX.Element {
    const {
        saving,
        keyMap,
        undoAction,
        redoAction,
        undoShortcut,
        redoShortcut,
        drawShortcut,
        switchToolsBlockerShortcut,
        activeControl,
        toolsBlockerState,
        onUndoClick,
        onRedoClick,
        onFinishDraw,
        onSwitchToolsBlockerState,
    } = props;

    const includesDoneButton = finishDrawAvailable(activeControl);

    const includesToolsBlockerButton =
        [ActiveControl.OPENCV_TOOLS, ActiveControl.AI_TOOLS].includes(activeControl) && toolsBlockerState.buttonVisible;

    const handlers: Record<keyof typeof componentShortcuts, (event?: KeyboardEvent) => void> = {
        UNDO: (event: KeyboardEvent | undefined) => {
            event?.preventDefault();
            onUndoClick();
        },
        REDO: (event: KeyboardEvent | undefined) => {
            event?.preventDefault();
            onRedoClick();
        },
        SWITCH_TOOLS_BLOCKER_STATE: (event: KeyboardEvent | undefined) => {
            event?.preventDefault();
            onSwitchToolsBlockerState();
        },
    };

    return (
        <>
            <GlobalHotKeys keyMap={subKeyMap(componentShortcuts, keyMap)} handlers={handlers} />
            { saving && (
                <Modal
                    open
                    destroyOnClose
                    className='cvat-saving-job-modal'
                    closable={false}
                    footer={[]}
                >
                    <Text>正在保存标注，请稍候</Text>
                    <LoadingOutlined />
                </Modal>
            )}
            <Col className='cvat-annotation-header-left-group'>
                <AnnotationMenuComponent />
                <SaveAnnotationsButton />
                <CVATTooltip overlay={`撤销：${localizeHistoryAction(undoAction)} ${undoShortcut}`}>
                    <Button
                        style={{ pointerEvents: undoAction ? 'initial' : 'none', opacity: undoAction ? 1 : 0.5 }}
                        type='link'
                        className='cvat-annotation-header-undo-button cvat-annotation-header-button'
                        onClick={onUndoClick}
                    >
                        <Icon component={UndoIcon} />
                        <span>撤销</span>
                    </Button>
                </CVATTooltip>
                <CVATTooltip overlay={`重做：${localizeHistoryAction(redoAction)} ${redoShortcut}`}>
                    <Button
                        style={{ pointerEvents: redoAction ? 'initial' : 'none', opacity: redoAction ? 1 : 0.5 }}
                        type='link'
                        className='cvat-annotation-header-redo-button cvat-annotation-header-button'
                        onClick={onRedoClick}
                    >
                        <Icon component={RedoIcon} />
                        重做
                    </Button>
                </CVATTooltip>
                {includesDoneButton ? (
                    <CVATTooltip overlay={`按 ${drawShortcut} 完成绘制`}>
                        <Button type='link' className='cvat-annotation-header-done-button cvat-annotation-header-button' onClick={onFinishDraw}>
                            <CheckCircleOutlined />
                            完成绘制
                        </Button>
                    </CVATTooltip>
                ) : null}
                {includesToolsBlockerButton ? (
                    <CVATTooltip overlay={`Press "${switchToolsBlockerShortcut}" to postpone running the algorithm `}>
                        <Button
                            type='link'
                            className={`cvat-annotation-header-block-tool-button cvat-annotation-header-button ${
                                toolsBlockerState.algorithmsLocked ? 'cvat-button-active' : ''
                            }`}
                            onClick={onSwitchToolsBlockerState}
                        >
                            <StopOutlined />
                            Block
                        </Button>
                    </CVATTooltip>
                ) : null}
            </Col>
        </>
    );
}

export default React.memo(LeftGroup);
