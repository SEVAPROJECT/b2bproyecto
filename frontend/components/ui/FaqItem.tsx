import React, { useState } from 'react';
import { ChevronDownIcon } from '../icons';
import { Faq } from '../../types/common';

interface FaqItemProps {
    faq: Faq;
}

const FaqItem: React.FC<FaqItemProps> = ({ faq }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="border-b border-slate-200 last:border-b-0">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full py-4 text-left flex items-center justify-between hover:bg-slate-50 transition-colors"
            >
                <span className="font-medium text-slate-900 pr-4">{faq.question}</span>
                <ChevronDownIcon 
                    className={`w-5 h-5 text-slate-500 transition-transform duration-200 ${
                        isOpen ? 'rotate-180' : ''
                    }`} 
                />
            </button>
            {isOpen && (
                <div className="pb-4 pr-8">
                    <p className="text-slate-600 leading-relaxed">{faq.answer}</p>
                </div>
            )}
        </div>
    );
};

export default FaqItem;
