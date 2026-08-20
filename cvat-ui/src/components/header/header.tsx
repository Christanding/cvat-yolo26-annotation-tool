// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';
import React from 'react';
import { connect } from 'react-redux';
import { useHistory, useLocation } from 'react-router';
import { Row, Col } from 'antd/lib/grid';
import { MenuProps } from 'antd/lib/menu';
import {
    SettingOutlined,
    InfoCircleOutlined,
    LoadingOutlined,
    LogoutOutlined,
    CaretDownOutlined,
    UserOutlined,
} from '@ant-design/icons';
import Layout from 'antd/lib/layout';
import Button from 'antd/lib/button';
import Dropdown from 'antd/lib/dropdown';
import Modal from 'antd/lib/modal';
import Text from 'antd/lib/typography/Text';

import config from 'config';

import CVATLogo from 'components/common/cvat-logo';
import { switchSettingsModalVisible as switchSettingsModalVisibleAction } from 'actions/settings-actions';
import { registerComponentShortcuts } from 'actions/shortcuts-actions';
import { AboutState, CombinedState } from 'reducers';
import GlobalHotKeys, { KeyMap } from 'utils/mousetrap-react';
import { ShortcutScope } from 'utils/enums';
import { subKeyMap } from 'utils/component-subkeymap';
import SettingsModal from './settings-modal/settings-modal';

interface StateToProps {
    user: any;
    about: AboutState;
    keyMap: KeyMap;
    switchSettingsShortcut: string;
    settingsModalVisible: boolean;
    logoutFetching: boolean;
}

interface DispatchToProps {
    switchSettingsModalVisible: (visible: boolean) => void;
}

const componentShortcuts = {
    SWITCH_SETTINGS: {
        name: '显示设置',
        description: '打开或关闭设置窗口',
        sequences: ['f2'],
        scope: ShortcutScope.GENERAL,
    },
};

registerComponentShortcuts(componentShortcuts);

function mapStateToProps(state: CombinedState): StateToProps {
    const {
        auth: { user, fetching: logoutFetching },
        about,
        shortcuts: { normalizedKeyMap, keyMap },
        settings: { showDialog: settingsModalVisible },
    } = state;

    return {
        user,
        about,
        switchSettingsShortcut: normalizedKeyMap.SWITCH_SETTINGS,
        keyMap,
        settingsModalVisible,
        logoutFetching,
    };
}

function mapDispatchToProps(dispatch: any): DispatchToProps {
    return {
        switchSettingsModalVisible: (visible: boolean): void => dispatch(
            switchSettingsModalVisibleAction(visible),
        ),
    };
}

type Props = StateToProps & DispatchToProps;

function HeaderComponent(props: Props): JSX.Element {
    const {
        user,
        about,
        keyMap,
        logoutFetching,
        settingsModalVisible,
        switchSettingsShortcut,
        switchSettingsModalVisible,
    } = props;

    const { LICENSE_URL, GITHUB_URL } = config;
    const history = useHistory();
    const location = useLocation();

    const handlers: Record<keyof typeof componentShortcuts, (event?: KeyboardEvent) => void> = {
        SWITCH_SETTINGS: (event: KeyboardEvent | undefined) => {
            if (event) event.preventDefault();
            switchSettingsModalVisible(!settingsModalVisible);
        },
    };

    const showAboutModal = (): void => {
        Modal.info({
            title: '关于 CVAT',
            content: (
                <div>
                    <p>本软件基于 CVAT Community 构建，遵循 MIT 许可证。</p>
                    <p>
                        <Text strong>服务端版本：</Text>
                        <Text type='secondary'>{` ${about.server.version}`}</Text>
                    </p>
                    <p>
                        <Text strong>界面版本：</Text>
                        <Text type='secondary'>{` ${about.packageVersion.ui}`}</Text>
                    </p>
                    <Row justify='space-around'>
                        <Col>
                            <a href={LICENSE_URL} target='_blank' rel='noopener noreferrer'>
                                MIT 许可证
                            </a>
                        </Col>
                        <Col>
                            <a href={GITHUB_URL} target='_blank' rel='noopener noreferrer'>
                                CVAT 上游源码
                            </a>
                        </Col>
                    </Row>
                </div>
            ),
            width: 600,
            okText: '关闭',
        });
    };

    const menuItems: MenuProps['items'] = [{
        key: 'settings',
        icon: <SettingOutlined />,
        onClick: () => switchSettingsModalVisible(true),
        title: `按 ${switchSettingsShortcut} 打开或关闭设置`,
        label: '设置',
    }, {
        key: 'about',
        icon: <InfoCircleOutlined />,
        onClick: showAboutModal,
        label: '关于',
    }, {
        key: 'logout',
        icon: logoutFetching ? <LoadingOutlined /> : <LogoutOutlined />,
        onClick: () => history.push('/auth/logout'),
        label: '退出登录',
        disabled: logoutFetching,
    }];

    const getButtonClassName = (name: string, path: string): string => {
        const baseClass = `cvat-header-${name}-button cvat-header-button`;
        return location.pathname === path ? `${baseClass} cvat-active-header-button` : baseClass;
    };

    return (
        <Layout.Header className='cvat-header'>
            <GlobalHotKeys keyMap={subKeyMap(componentShortcuts, keyMap)} handlers={handlers} />
            <div className='cvat-left-header'>
                <CVATLogo />
                <Button
                    className={getButtonClassName('tasks', '/tasks')}
                    type='link'
                    href='/tasks?page=1'
                    onClick={(event: React.MouseEvent): void => {
                        event.preventDefault();
                        history.push('/tasks');
                    }}
                >
                    任务列表
                </Button>
                <Button
                    className={getButtonClassName('create-task', '/tasks/create')}
                    type='link'
                    href='/tasks/create'
                    onClick={(event: React.MouseEvent): void => {
                        event.preventDefault();
                        history.push('/tasks/create');
                    }}
                >
                    新建任务
                </Button>
                <Button
                    className={getButtonClassName('video-extraction', '/videos/extract')}
                    type='link'
                    href='/videos/extract'
                    onClick={(event: React.MouseEvent): void => {
                        event.preventDefault();
                        history.push('/videos/extract');
                    }}
                >
                    视频抽帧
                </Button>
                <Button
                    className={getButtonClassName('package-import', '/packages/import')}
                    type='link'
                    href='/packages/import'
                    onClick={(event: React.MouseEvent): void => {
                        event.preventDefault();
                        history.push('/packages/import');
                    }}
                >
                    导入
                </Button>
            </div>
            <div className='cvat-right-header'>
                <Dropdown
                    trigger={['click']}
                    destroyPopupOnHide
                    placement='bottomRight'
                    menu={{
                        items: menuItems,
                        className: 'cvat-header-menu',
                    }}
                    className='cvat-header-menu-user-dropdown'
                >
                    <span>
                        <UserOutlined className='cvat-header-dropdown-icon' />
                        <Row>
                            <Col span={24}>
                                <Text strong className='cvat-header-menu-user-dropdown-user'>
                                    {user.username.length > 14 ? `${user.username.slice(0, 10)} ...` : user.username}
                                </Text>
                            </Col>
                        </Row>
                        <CaretDownOutlined className='cvat-header-dropdown-icon' />
                    </span>
                </Dropdown>
            </div>
            <SettingsModal
                visible={settingsModalVisible}
                onClose={() => switchSettingsModalVisible(false)}
            />
        </Layout.Header>
    );
}

export default connect(mapStateToProps, mapDispatchToProps)(React.memo(HeaderComponent));
