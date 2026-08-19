// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';
import React, { Dispatch, TransitionEvent } from 'react';
import { AnyAction } from 'redux';
import { connect } from 'react-redux';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import Tabs from 'antd/lib/tabs';
import Layout from 'antd/lib/layout';

import { CombinedState } from 'reducers';
import { collapseSidebar as collapseSidebarAction } from 'actions/annotation-actions';

interface OwnProps {
    objectsList: JSX.Element;
}

interface StateToProps {
    sidebarCollapsed: boolean;
}

interface DispatchToProps {
    collapseSidebar(): void;
}

function mapStateToProps(state: CombinedState): StateToProps {
    return { sidebarCollapsed: state.annotation.sidebarCollapsed };
}

function mapDispatchToProps(dispatch: Dispatch<AnyAction>): DispatchToProps {
    return { collapseSidebar: () => dispatch(collapseSidebarAction()) };
}

function ObjectsSideBar(props: StateToProps & DispatchToProps & OwnProps): JSX.Element {
    const { sidebarCollapsed, collapseSidebar, objectsList } = props;
    const collapse = (): void => {
        const [collapser] = window.document.getElementsByClassName('cvat-objects-sidebar');
        const listener = (event: TransitionEvent): void => {
            if (event.target && event.propertyName === 'width' && event.target === collapser) {
                window.dispatchEvent(new Event('resize'));
                (collapser as HTMLElement).removeEventListener('transitionend', listener as any);
            }
        };
        if (collapser) (collapser as HTMLElement).addEventListener('transitionend', listener as any);
        collapseSidebar();
    };

    return (
        <Layout.Sider
            className='cvat-objects-sidebar'
            theme='light'
            width={320}
            collapsedWidth={0}
            reverseArrow
            collapsible
            trigger={null}
            collapsed={sidebarCollapsed}
        >
            {/* eslint-disable-next-line */}
            <span className='cvat-objects-sidebar-sider' onClick={collapse}>
                {sidebarCollapsed ? <MenuFoldOutlined title='显示对象列表' /> : <MenuUnfoldOutlined title='隐藏对象列表' />}
            </span>
            <Tabs
                type='card'
                className='cvat-objects-sidebar-tabs'
                items={[{ key: 'objects', label: '标注', children: objectsList }]}
            />
        </Layout.Sider>
    );
}

export default connect(mapStateToProps, mapDispatchToProps)(React.memo(ObjectsSideBar));
