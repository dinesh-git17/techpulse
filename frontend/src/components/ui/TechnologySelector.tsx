"use client";

/**
 * @fileoverview Multi-select combobox for technology filtering.
 *
 * Design rationale: Uses Radix UI Popover as the dropdown primitive with
 * custom listbox semantics built on top. Implements WAI-ARIA combobox pattern
 * with full keyboard navigation. Selected items render as removable tags
 * with accessible remove buttons.
 */
import {
  type KeyboardEvent,
  type ReactNode,
  useCallback,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import * as Popover from "@radix-ui/react-popover";

/** Maximum number of technologies that can be selected. */
const MAX_SELECTIONS = 10;

/**
 * Represents a selectable technology option.
 */
export interface TechnologyOption {
  /** Unique identifier for the technology. */
  id: string;
  /** Display name shown in the UI. */
  name: string;
}

/**
 * Props for the TechnologySelector component.
 */
export interface TechnologySelectorProps {
  /** Array of currently selected technology IDs. */
  selectedIds: string[];

  /** All available technology options to select from. */
  availableOptions: TechnologyOption[];

  /** Callback fired when the selection changes. */
  onChange: (newIds: string[]) => void;

  /** Disables the entire selector when true. */
  disabled?: boolean;
}

/**
 * Renders a multi-select combobox for selecting technologies.
 *
 * Supports keyboard navigation (Tab, Arrow keys, Enter, Escape), search
 * filtering, and displays selected items as removable tags. Enforces a
 * maximum of 10 selections.
 *
 * @param props.selectedIds - Currently selected technology IDs.
 * @param props.availableOptions - All available options to select from.
 * @param props.onChange - Callback when selection changes.
 * @param props.disabled - Disables the selector when true.
 *
 * @example
 * ```tsx
 * <TechnologySelector
 *   selectedIds={["python", "typescript"]}
 *   availableOptions={[
 *     { id: "python", name: "Python" },
 *     { id: "typescript", name: "TypeScript" },
 *     { id: "rust", name: "Rust" },
 *   ]}
 *   onChange={(ids) => setSelectedIds(ids)}
 * />
 * ```
 */
export function TechnologySelector({
  selectedIds,
  availableOptions,
  onChange,
  disabled = false,
}: TechnologySelectorProps): ReactNode {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const instanceId = useId();
  const listboxId = `${instanceId}-listbox`;
  const inputId = `${instanceId}-input`;

  const isAtLimit = selectedIds.length >= MAX_SELECTIONS;

  const selectedOptionsMap = useMemo(() => {
    return new Map(
      availableOptions
        .filter((opt) => selectedIds.includes(opt.id))
        .map((opt) => [opt.id, opt]),
    );
  }, [availableOptions, selectedIds]);

  const filteredOptions = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    return availableOptions.filter((option) => {
      const matchesSearch =
        query === "" || option.name.toLowerCase().includes(query);
      const isNotSelected = !selectedIds.includes(option.id);
      return matchesSearch && isNotSelected;
    });
  }, [availableOptions, searchQuery, selectedIds]);

  const handleSelect = useCallback(
    (optionId: string) => {
      if (isAtLimit) return;
      onChange([...selectedIds, optionId]);
      setSearchQuery("");
      setActiveIndex(-1);
      inputRef.current?.focus();
    },
    [isAtLimit, onChange, selectedIds],
  );

  const handleRemove = useCallback(
    (optionId: string) => {
      onChange(selectedIds.filter((id) => id !== optionId));
      inputRef.current?.focus();
    },
    [onChange, selectedIds],
  );

  const handleInputKeyDown = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      switch (event.key) {
        case "ArrowDown": {
          event.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
            setActiveIndex(0);
          } else {
            setActiveIndex((prev) =>
              prev < filteredOptions.length - 1 ? prev + 1 : prev,
            );
          }
          break;
        }
        case "ArrowUp": {
          event.preventDefault();
          setActiveIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        }
        case "Enter": {
          event.preventDefault();
          const activeOption = filteredOptions[activeIndex];
          if (activeOption && !isAtLimit) {
            handleSelect(activeOption.id);
          }
          break;
        }
        case "Escape": {
          event.preventDefault();
          setIsOpen(false);
          setActiveIndex(-1);
          break;
        }
        case "Backspace": {
          if (searchQuery === "" && selectedIds.length > 0) {
            const lastId = selectedIds[selectedIds.length - 1];
            if (lastId) {
              handleRemove(lastId);
            }
          }
          break;
        }
      }
    },
    [
      isOpen,
      filteredOptions,
      activeIndex,
      isAtLimit,
      handleSelect,
      searchQuery,
      selectedIds,
      handleRemove,
    ],
  );

  const handleOptionKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>, optionId: string) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        if (!isAtLimit) {
          handleSelect(optionId);
        }
      }
    },
    [handleSelect, isAtLimit],
  );

  return (
    <div className="w-full">
      <label
        htmlFor={inputId}
        className="mb-2 block text-sm font-medium text-[var(--text-primary)]"
      >
        Technologies
        {isAtLimit && (
          <span className="ml-2 text-xs text-[var(--text-muted)]">
            (maximum {MAX_SELECTIONS} selected)
          </span>
        )}
      </label>

      <Popover.Root open={isOpen} onOpenChange={setIsOpen}>
        <Popover.Anchor asChild>
          <div
            className={`
              flex
              min-h-[44px]
              flex-wrap
              items-center
              gap-2
              rounded-md
              border
              border-[var(--border-default)]
              bg-[var(--bg-primary)]
              px-3
              py-2
              transition-colors
              focus-within:border-[var(--accent-primary)]
              focus-within:outline
              focus-within:outline-2
              focus-within:outline-offset-2
              focus-within:outline-[var(--accent-primary)]
              ${disabled ? "cursor-not-allowed opacity-50" : ""}
            `}
          >
            {selectedIds.map((id) => {
              const option = selectedOptionsMap.get(id);
              if (!option) return null;
              return (
                <span
                  key={id}
                  className="
                    inline-flex
                    items-center
                    gap-1
                    rounded
                    bg-[var(--bg-tertiary)]
                    px-2
                    py-1
                    text-sm
                    text-[var(--text-primary)]
                  "
                >
                  {option.name}
                  <button
                    type="button"
                    onClick={() => handleRemove(id)}
                    disabled={disabled}
                    aria-label={`Remove ${option.name}`}
                    className="
                      ml-1
                      inline-flex
                      h-4
                      w-4
                      items-center
                      justify-center
                      rounded
                      text-[var(--text-muted)]
                      transition-colors
                      hover:bg-[var(--border-default)]
                      hover:text-[var(--text-primary)]
                      focus:outline
                      focus:outline-2
                      focus:outline-[var(--accent-primary)]
                    "
                  >
                    <span aria-hidden="true">&times;</span>
                  </button>
                </span>
              );
            })}

            <input
              ref={inputRef}
              id={inputId}
              type="text"
              role="combobox"
              aria-expanded={isOpen}
              aria-controls={listboxId}
              aria-activedescendant={
                activeIndex >= 0
                  ? `${instanceId}-option-${activeIndex}`
                  : undefined
              }
              aria-autocomplete="list"
              aria-label="Search technologies"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!isOpen) setIsOpen(true);
                setActiveIndex(0);
              }}
              onFocus={() => setIsOpen(true)}
              onKeyDown={handleInputKeyDown}
              disabled={disabled}
              placeholder={
                selectedIds.length === 0 ? "Select technologies..." : ""
              }
              className="
                min-w-[120px]
                flex-1
                border-none
                bg-transparent
                text-sm
                text-[var(--text-primary)]
                placeholder:text-[var(--text-muted)]
                focus:outline-none
              "
            />
          </div>
        </Popover.Anchor>

        <Popover.Portal>
          <Popover.Content
            className="
              z-50
              mt-1
              max-h-[300px]
              w-[var(--radix-popover-trigger-width)]
              overflow-auto
              rounded-md
              border
              border-[var(--border-default)]
              bg-[var(--bg-primary)]
              shadow-lg
            "
            onOpenAutoFocus={(e) => e.preventDefault()}
            sideOffset={4}
          >
            <div
              ref={listRef}
              id={listboxId}
              role="listbox"
              aria-label="Available technologies"
              aria-multiselectable="true"
              className="py-1"
            >
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-[var(--text-muted)]">
                  {searchQuery
                    ? "No technologies found"
                    : "All technologies selected"}
                </div>
              ) : (
                filteredOptions.map((option, index) => {
                  const isActive = index === activeIndex;
                  const isDisabled = isAtLimit;

                  return (
                    <div
                      key={option.id}
                      id={`${instanceId}-option-${index}`}
                      role="option"
                      aria-selected={false}
                      aria-disabled={isDisabled}
                      tabIndex={-1}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => {
                        if (!isDisabled) handleSelect(option.id);
                      }}
                      onKeyDown={(e) => handleOptionKeyDown(e, option.id)}
                      className={`
                        cursor-pointer
                        px-3
                        py-2
                        text-sm
                        ${
                          isActive
                            ? "bg-[var(--bg-secondary)] text-[var(--text-primary)]"
                            : "text-[var(--text-primary)]"
                        }
                        ${
                          isDisabled
                            ? "cursor-not-allowed opacity-50"
                            : "hover:bg-[var(--bg-secondary)]"
                        }
                      `}
                    >
                      {option.name}
                    </div>
                  );
                })
              )}
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
}
