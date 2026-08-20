// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';

import { useDraggable } from '@dnd-kit/core';
import {
    CaretDownOutlined, CaretRightOutlined, EyeInvisibleOutlined,
    EyeOutlined, HolderOutlined, SelectOutlined,
} from '@ant-design/icons';
import Button from 'antd/lib/button';
import Text from 'antd/lib/typography/Text';

import CVATTooltip from 'components/common/cvat-tooltip';
import { layerDragID } from './index';

interface LayerHeaderProps {
    zOrder: number;
    selected: boolean;
    visible: boolean;
    collapsed: boolean;
    selectLayer(zOrder: number): void;
    toggleLayerCollapsed(zOrder: number): void;
}

// Renders layer controls and exposes the layer itself as a draggable handle target.
function LayerHeader(props: LayerHeaderProps): JSX.Element {
    const {
        zOrder, selected, visible, collapsed, selectLayer, toggleLayerCollapsed,
    } = props;

    const {
        attributes, listeners, setNodeRef, isDragging,
    } = useDraggable({ id: layerDragID(zOrder) });

    const style = isDragging ? { pointerEvents: 'none' as const } : {};

    const className = [
        'cvat-objects-sidebar-z-layer-mark',
        ...(isDragging ? ['cvat-objects-sidebar-z-layer-mark-dragging'] : []),
        ...(!visible ? ['cvat-objects-sidebar-z-layer-mark-invisible'] : []),
    ].join(' ');

    const visibilityTooltip = visible ? '已在画布上显示' : '已在画布上隐藏';
    const selectLayerTooltip = selected ? '当前图层；更高图层已隐藏' :
        '设为当前图层；更高图层将被隐藏';

    return (
        <div
            ref={setNodeRef}
            className={className}
            style={style}
        >
            <div>
                <CVATTooltip title={collapsed ? '展开图层' : '折叠图层'}>
                    <Button
                        className='cvat-objects-sidebar-z-layer-collapse-button'
                        type='text'
                        size='small'
                        icon={collapsed ? <CaretRightOutlined /> : <CaretDownOutlined />}
                        onClick={(): void => toggleLayerCollapsed(zOrder)}
                    />
                </CVATTooltip>
                <CVATTooltip title={selectLayerTooltip}>
                    <Button
                        className='cvat-objects-sidebar-z-layer-select-button'
                        type='text'
                        size='small'
                        icon={<SelectOutlined />}
                        onClick={(): void => selectLayer(zOrder)}
                    />
                </CVATTooltip>
                <CVATTooltip title='拖动图层'>
                    <Button
                        {...attributes}
                        {...listeners}
                        className='cvat-objects-sidebar-z-layer-drag-handle'
                        type='text'
                        size='small'
                        icon={<HolderOutlined />}
                    />
                </CVATTooltip>
            </div>
            <div className='cvat-objects-sidebar-z-layer-id'>
                <Text strong>{zOrder}</Text>
                <CVATTooltip title={visibilityTooltip}>
                    <span className='cvat-objects-sidebar-z-layer-visibility-indicator'>
                        {visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                    </span>
                </CVATTooltip>
            </div>
        </div>
    );
}

export default React.memo(LayerHeader);
