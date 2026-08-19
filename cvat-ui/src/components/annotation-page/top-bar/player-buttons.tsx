// Copyright (C) 2020-2024 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React, { useEffect } from 'react';
import { Col } from 'antd/lib/grid';
import Icon from '@ant-design/icons';
import CVATTooltip from 'components/common/cvat-tooltip';
import { KeyMap } from 'utils/mousetrap-react';
import { NavigationType, Workspace } from 'reducers';
import { FirstIcon, LastIcon, NextIcon, PreviousIcon } from 'icons';
import { Chapter } from 'cvat-core/src/frames';

interface Props {
    playing: boolean;
    playPauseShortcut: string;
    nextFrameShortcut: string;
    previousFrameShortcut: string;
    forwardShortcut: string;
    backwardShortcut: string;
    chapters: Chapter[];
    keyMap: KeyMap;
    workspace: Workspace;
    navigationType: NavigationType;
    onSwitchPlay(): void;
    onPrevFrame(): void;
    onNextFrame(): void;
    onForward(): void;
    onBackward(): void;
    onFirstFrame(): void;
    onLastFrame(): void;
    onSearchAnnotations(direction: 'forward' | 'backward'): void;
    onSearchChapters(direction: 'forward' | 'backward'): void;
    onHoveredChapter(id: number | null): void;
    onSelectChapter(id: number): void;
    setNavigationType(navigationType: NavigationType): void;
}

export default function PlayerButtons(props: Props): JSX.Element {
    const {
        onFirstFrame, onPrevFrame, onNextFrame, onLastFrame,
    } = props;

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent): void => {
            const target = event.target as HTMLElement | null;
            const editingText = target?.matches('input, textarea, [contenteditable="true"]');
            if (editingText || event.ctrlKey || event.metaKey || event.altKey) return;
            if (event.key.toLowerCase() === 'a') {
                event.preventDefault();
                onPrevFrame();
            } else if (event.key.toLowerCase() === 'd') {
                event.preventDefault();
                onNextFrame();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onPrevFrame, onNextFrame]);

    return (
        <Col className='cvat-player-buttons'>
            <CVATTooltip title='第一张图片'>
                <Icon className='cvat-player-first-button' component={FirstIcon} onClick={onFirstFrame} />
            </CVATTooltip>
            <CVATTooltip title='上一张图片 A'>
                <Icon className='cvat-player-previous-button' component={PreviousIcon} onClick={onPrevFrame} />
            </CVATTooltip>
            <CVATTooltip title='下一张图片 D'>
                <Icon className='cvat-player-next-button' component={NextIcon} onClick={onNextFrame} />
            </CVATTooltip>
            <CVATTooltip title='最后一张图片'>
                <Icon className='cvat-player-last-button' component={LastIcon} onClick={onLastFrame} />
            </CVATTooltip>
        </Col>
    );
}
