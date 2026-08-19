// SPDX-License-Identifier: MIT

import './styles.scss';
import React, { useEffect, useState } from 'react';
import { useHistory } from 'react-router';
import { InboxOutlined } from '@ant-design/icons';
import Alert from 'antd/lib/alert';
import Button from 'antd/lib/button';
import Card from 'antd/lib/card';
import Col from 'antd/lib/col';
import Form from 'antd/lib/form';
import Input from 'antd/lib/input';
import Progress from 'antd/lib/progress';
import Row from 'antd/lib/row';
import Upload, { RcFile } from 'antd/lib/upload';
import Text from 'antd/lib/typography/Text';
import notification from 'antd/lib/notification';

import { createPackageImport, getPackageImport } from 'utils/local-api';

export default function PackageImportPage(): JSX.Element {
    const history = useHistory();
    const [taskName, setTaskName] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [jobID, setJobID] = useState<string>();
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');

    useEffect(() => {
        if (!jobID) return undefined;
        let stopped = false;
        let timer: number | undefined;

        const poll = async (): Promise<void> => {
            try {
                const status = await getPackageImport(jobID);
                if (stopped) return;
                setProgress(status.progress);
                setStatusMessage(status.message || '');
                if (status.status === 'finished' && status.result) {
                    notification.success({ message: '标注包导入完成' });
                    history.push(`/tasks/${status.result.task_id}`);
                } else if (status.status === 'failed') {
                    setJobID(undefined);
                    notification.error({ message: '标注包导入失败', description: status.error });
                } else {
                    timer = window.setTimeout(poll, 1000);
                }
            } catch (error: any) {
                if (!stopped) {
                    setJobID(undefined);
                    notification.error({ message: '无法获取导入进度', description: error.message });
                }
            }
        };

        poll();
        return () => {
            stopped = true;
            if (timer) window.clearTimeout(timer);
        };
    }, [history, jobID]);

    const startImport = async (): Promise<void> => {
        const name = taskName.trim();
        if (!name || !file) {
            notification.warning({ message: '请填写任务名称并选择 ZIP 标注包' });
            return;
        }
        setProgress(0);
        setStatusMessage('');
        try {
            const job = await createPackageImport(name, file);
            setJobID(job.id);
        } catch (error: any) {
            notification.error({ message: '无法开始导入', description: error.message });
        }
    };

    return (
        <Row justify='center' align='top' className='cvat-package-import-page'>
            <Col md={20} lg={16} xl={14} xxl={12}>
                <Text className='cvat-title'>导入待划分标注包</Text>
                <Card>
                    <Alert
                        type='info'
                        showIcon
                        message='ZIP 必须包含 images、labels 和仅记录类别的 data.yaml。导入后会创建一个新任务。'
                    />
                    <Form layout='vertical'>
                        <Form.Item label='任务名称' required>
                            <Input
                                value={taskName}
                                maxLength={256}
                                disabled={Boolean(jobID)}
                                placeholder='输入新任务名称'
                                onChange={(event) => setTaskName(event.target.value)}
                            />
                        </Form.Item>
                        <Form.Item label='标注包' required>
                            <Upload.Dragger
                                accept='.zip,application/zip'
                                fileList={file ? [file] as any[] : []}
                                disabled={Boolean(jobID)}
                                maxCount={1}
                                beforeUpload={(selectedFile: RcFile): boolean => {
                                    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
                                        notification.error({ message: '请选择 ZIP 标注包' });
                                    } else {
                                        setFile(selectedFile);
                                    }
                                    return false;
                                }}
                                onRemove={() => {
                                    setFile(null);
                                }}
                            >
                                <p className='ant-upload-drag-icon'><InboxOutlined /></p>
                                <p className='ant-upload-text'>点击选择，或将 ZIP 标注包拖到这里</p>
                            </Upload.Dragger>
                        </Form.Item>
                        {jobID ? (
                            <Progress percent={progress} status='active' format={() => statusMessage || `${progress}%`} />
                        ) : null}
                        <Button
                            type='primary'
                            loading={Boolean(jobID)}
                            disabled={!taskName.trim() || !file}
                            onClick={startImport}
                        >
                            导入并创建任务
                        </Button>
                    </Form>
                </Card>
            </Col>
        </Row>
    );
}
