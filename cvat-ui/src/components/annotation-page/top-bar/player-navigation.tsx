// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React, { useEffect, useState } from 'react';
import { Row, Col } from 'antd/lib/grid';
import Slider from 'antd/lib/slider';
import InputNumber from 'antd/lib/input-number';
import Text from 'antd/lib/typography/Text';

import { Workspace } from 'reducers';
import CVATTooltip from 'components/common/cvat-tooltip';
import { clamp } from 'utils/math';
import { KeyMap } from 'utils/mousetrap-react';
import { Chapter } from 'cvat-core/src/frames';

interface Props {
    startFrame: number;
    stopFrame: number;
    playing: boolean;
    ranges: string;
    frameNumber: number;
    chapters: Chapter[] | null;
    hoveredChapter: number | null;
    frameFilename: string;
    frameDeleted: boolean;
    deleteFrameShortcut: string;
    focusFrameInputShortcut: string;
    searchFrameByNameShortcut: string;
    showSearchFrameByName: boolean;
    inputFrameRef: React.RefObject<HTMLInputElement>;
    keyMap: KeyMap;
    workspace: Workspace;
    onSliderChange(value: number): void;
    onInputChange(value: number): void;
    onURLIconClick(): void;
    onCopyFilenameIconClick(): void;
    onDeleteFrame(): void;
    onRestoreFrame(): void;
    switchNavigationBlocked(blocked: boolean): void;
    switchShowSearchPallet(visible: boolean): void;
}

export default function PlayerNavigation(props: Props): JSX.Element {
    const {
        startFrame, stopFrame, frameNumber, frameFilename, inputFrameRef,
        workspace, onSliderChange, onInputChange,
    } = props;
    const [frameInputValue, setFrameInputValue] = useState(frameNumber);

    useEffect(() => {
        setFrameInputValue(frameNumber);
    }, [frameNumber]);

    return (
        <>
            <Col className='cvat-player-controls'>
                <Row align='bottom'>
                    <Col style={{ position: 'relative' }}>
                        <Slider
                            className='cvat-player-slider'
                            min={startFrame}
                            max={stopFrame}
                            value={frameNumber || 0}
                            onChange={workspace !== Workspace.SINGLE_SHAPE ? onSliderChange : undefined}
                        />
                    </Col>
                </Row>
                <Row justify='center'>
                    <Col className='cvat-player-filename-wrapper'>
                        <CVATTooltip title={frameFilename}>
                            <Text type='secondary'>{frameFilename}</Text>
                        </CVATTooltip>
                    </Col>
                </Row>
            </Col>
            <Col>
                <CVATTooltip title='输入图片序号并按回车键切换'>
                    <InputNumber
                        ref={inputFrameRef}
                        className='cvat-player-frame-selector'
                        type='number'
                        disabled={workspace === Workspace.SINGLE_SHAPE}
                        value={frameInputValue}
                        min={startFrame}
                        max={stopFrame}
                        style={{ ['--frame-input-width' as string]: `${stopFrame.toString().length + 2}ch` }}
                        onChange={(value: number | undefined | string | null) => {
                            if (typeof value !== 'undefined' && value !== null) {
                                setFrameInputValue(Math.floor(clamp(+value, startFrame, stopFrame)));
                            }
                        }}
                        onFocus={() => inputFrameRef.current?.select()}
                        onBlur={() => onInputChange(frameInputValue)}
                        onPressEnter={() => onInputChange(frameInputValue)}
                    />
                </CVATTooltip>
            </Col>
        </>
    );
}
